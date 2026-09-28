using System;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ModLoader;

namespace FlyMind.Vision
{
    /// <summary>
    /// A real third-person window into the fly's world: the fly's eye view is rendered
    /// from its own position into a RenderTarget2D, at its own heading, and then shown
    /// on screen as a panel (bottom right, under the brain scan).
    ///
    /// "Third person" here means the camera sits *behind and above* the fly's head, so
    /// the fly itself is drawn in the frame - the same relationship the player's camera
    /// has to the player, just flat and much smaller, because the fly is 8 pixels tall.
    ///
    /// Tile textures that vanilla has not loaded are simply skipped instead of forcing
    /// them, so this never stalls the frame.
    /// </summary>
    public static class FlyEyeView
    {
        public const int Width = 320;
        public const int Height = 180;
        public const float PixelsPerTile = 6f;      // zoom: 320 / 6 鈮?53 tiles across
        private const float EyeHeightTiles = 2.2f;  // camera sits this far "above" the fly

        public static bool Enabled = true;

        /// <summary>
        /// Whether the fly's own body is drawn into its own visual field.  True is the mod's
        /// normal third-person view (an input no real fly ever has); the self-observation
        /// experiment clears it for the natural and placebo arms.
        /// </summary>
        public static bool RenderOwnBody = true;

        private static RenderTarget2D _target;
        private static SpriteBatch _batch;

        public static Texture2D Target => _target;

        /// <summary>
        /// Fraction of the eye view taken up by the fly's own body (0..1), refreshed each
        /// render.  This is the geometric fact the fly's eyes are reporting: part of the
        /// image in front of it is itself.  It is *not* the fly seeing its own brain.
        /// </summary>
        public static float SelfInView { get; private set; }

        /// <summary>How much the view changed since the last render (0..1), from the framebuffer.</summary>
        public static float ViewMotion { get; private set; }

        /// <summary>Screen rectangle (in eye-view pixels) where the fly's body is drawn.</summary>
        public static Rectangle SelfRect { get; private set; }

        /// <summary>
        /// The fly's body projected into the view, as a coarse occupancy grid
        /// (GridCols x GridRows).  Used both for the self-view fraction and so the HUD can
        /// show which part of the retina is "me".
        /// </summary>
        public const int GridCols = 16;
        public const int GridRows = 9;
        public static readonly float[] SelfGrid = new float[GridCols * GridRows];

        private static byte[] _previousFrame;
        private static byte[] _readback;

        public static void EnsureDevice()
        {
            var device = Main.graphics.GraphicsDevice;
            if (device == null) return;
            if (_target == null || _target.IsDisposed)
            {
                _target?.Dispose();
                _target = new RenderTarget2D(device, Width, Height, false,
                    SurfaceFormat.Color, DepthFormat.None, 0, RenderTargetUsage.PreserveContents);
            }
            if (_batch == null || _batch.IsDisposed)
                _batch = new SpriteBatch(device);
        }

        public static void Dispose()
        {
            _target?.Dispose();
            _target = null;
            _batch?.Dispose();
            _batch = null;
        }

        /// <summary>Render one frame of the fly's view. Safe to call every tick.</summary>
        public static void Render(FlyAgent agent)
        {
            if (!Enabled || Main.dedServ || agent == null || agent.Npc == null) return;
            EnsureDevice();
            if (_target == null || _batch == null) return;

            var device = Main.graphics.GraphicsDevice;
            var previousTargets = device.GetRenderTargets();

            Vector2 eye = agent.Npc.Center;
            // camera = behind the fly along its heading, raised by a fixed amount
            Vector2 cam = eye - new Vector2((float)Math.Cos(agent.Heading), (float)Math.Sin(agent.Heading))
                              * (Width * 0.16f) - new Vector2(0f, EyeHeightTiles * PixelsPerTile);
            Vector2 center = new Vector2(Width * 0.5f, Height * 0.5f);

            // where the fly's own body lands in this frame, before drawing it
            var bodyPos = ToScreen(eye, cam, center);
            float bodyScale = PixelsPerTile / 16f * 1.8f;
            int bodyW = Math.Max(4, (int)(12 * bodyScale * 1.4f));
            int bodyH = Math.Max(4, (int)(12 * bodyScale));
            SelfRect = new Rectangle((int)bodyPos.X - bodyW / 2, (int)bodyPos.Y - bodyH / 2, bodyW, bodyH);

            try
            {
                device.SetRenderTarget(_target);
                device.Clear(new Color(10, 12, 18));

                _batch.Begin(SpriteSortMode.Deferred, BlendState.AlphaBlend,
                    SamplerState.PointClamp, DepthStencilState.None, RasterizerState.CullNone);

                DrawTiles(_batch, cam, center);
                // The fly's own body is drawn into its own visual field only when it is
                // meant to be there.  The self-observation experiment turns it off for the
                // natural and placebo arms, so the fly then looks at the same world a real
                // fly would see.
                if (RenderOwnBody)
                {
                    DrawFly(_batch, agent, cam, center);
                    DrawFliesAndPlayers(_batch, agent, cam, center);
                }

                _batch.End();
            }
            catch (Exception e)
            {
                ModContent.GetInstance<FlyMind>()?.Logger.Warn("FlyEyeView render failed: " + e.Message);
                Enabled = false;
            }
            finally
            {
                if (previousTargets.Length > 0 && previousTargets[0].RenderTarget != null)
                    device.SetRenderTarget((RenderTarget2D)previousTargets[0].RenderTarget);
                else
                    device.SetRenderTarget(null);
            }

            UpdateSelfPerception(device);
        }

        /// <summary>
        /// Read the frame back and work out what the retina is being told: how much of the
        /// image is the fly's own body, and how much the rest of the image moved since the
        /// last frame.  The read-back is throttled (a few times a second) because pulling
        /// the framebuffer back to the CPU is not free, and the fly's own visual latency
        /// is tens of milliseconds anyway.
        /// </summary>
        private static void UpdateSelfPerception(GraphicsDevice device)
        {
            // self occupancy: geometric, cheap, every frame.  With the body not rendered the
            // fly is not in its own visual field at all, so the occupancy grid is empty -
            // this is what the natural and placebo arms of the experiment measure.
            int filled = 0;
            if (!RenderOwnBody)
            {
                Array.Clear(SelfGrid, 0, SelfGrid.Length);
                SelfInView = 0f;
            }
            else
            {
                for (int gy = 0; gy < GridRows; gy++)
                {
                    for (int gx = 0; gx < GridCols; gx++)
                    {
                        float cx = (gx + 0.5f) * Width / GridCols;
                        float cy = (gy + 0.5f) * Height / GridRows;
                        bool mine = cx >= SelfRect.Left && cx < SelfRect.Right
                                    && cy >= SelfRect.Top && cy < SelfRect.Bottom;
                        SelfGrid[gy * GridCols + gx] = mine ? 1f : 0f;
                        if (mine) filled++;
                    }
                }
                SelfInView = filled / (float)(GridCols * GridRows);
            }

            // retinal motion: frame-to-frame difference on the GPU read-back
            _frameCounter++;
            if (_frameCounter % ReadbackEvery != 0) return;

            int bytes = Width * Height * 4;
            _readback ??= new byte[bytes];
            try
            {
                _target.GetData(_readback);
            }
            catch (Exception)
            {
                // GetData is not always allowed on the render target in use; motion then
                // simply falls back to the geometric self-view term
                return;
            }

            if (_previousFrame == null || _previousFrame.Length != bytes)
            {
                _previousFrame = new byte[bytes];
                Buffer.BlockCopy(_readback, 0, _previousFrame, 0, bytes);
                ViewMotion = 0f;
                return;
            }

            long diff = 0;
            for (int i = 0; i < bytes; i += MotionStride)
            {
                int d = _readback[i] - _previousFrame[i];
                if (d < 0) d = -d;
                diff += d;
            }
            Buffer.BlockCopy(_readback, 0, _previousFrame, 0, bytes);

            int samples = bytes / MotionStride;
            float normalized = diff / (float)(samples * 255);
            // smooth: the fly's LPTCs integrate over ~10s of ms
            ViewMotion = MathHelper.Clamp(ViewMotion * 0.6f + normalized * 4f * 0.4f, 0f, 1f);
        }

        private static int _frameCounter;
        private const int ReadbackEvery = 4;    // ~15 Hz at 60 fps
        private const int MotionStride = 64;    // sample every 16th pixel, one channel

        private static void DrawTiles(SpriteBatch sb, Vector2 cam, Vector2 center)
        {
            int tilesX = (int)(Width / PixelsPerTile) + 2;
            int tilesY = (int)(Height / PixelsPerTile) + 2;
            int startX = (int)(cam.X / 16f) - tilesX / 2;
            int startY = (int)(cam.Y / 16f) - tilesY / 2;

            // two passes so solid tiles land on top of background ones
            for (int pass = 0; pass < 2; pass++)
            {
                bool solidPass = pass == 1;
                for (int ty = startY; ty < startY + tilesY; ty++)
                {
                    for (int tx = startX; tx < startX + tilesX; tx++)
                    {
                        if (!WorldGen.InWorld(tx, ty, 4)) continue;
                        Tile tile = Main.tile[tx, ty];
                        if (tile == null || !tile.HasTile) continue;
                        if (Main.tileSolid[tile.TileType] != solidPass) continue;
                        if (tile.TileType >= TextureAssets.Tile.Length) continue;
                        var asset = TextureAssets.Tile[tile.TileType];
                        if (asset == null) continue;
                        Texture2D sheet = asset.Value;
                        if (sheet == null) continue;

                        int frameX = tile.TileFrameX;
                        int frameY = tile.TileFrameY;
                        if (frameX < 0 || frameY < 0) continue;
                        int col = frameX / 18;
                        int row = frameY / 18;
                        if (col * 18 + 16 > sheet.Width || row * 18 + 16 > sheet.Height) continue;

                        var src = new Rectangle(col * 18, row * 18, 16, 16);
                        var pos = new Vector2(
                            center.X + (tx * 16f + 8f - cam.X) / 16f * PixelsPerTile - PixelsPerTile * 0.5f,
                            center.Y + (ty * 16f + 8f - cam.Y) / 16f * PixelsPerTile - PixelsPerTile * 0.5f);

                        Color color = Lighting.GetColor(tx, ty);
                        sb.Draw(sheet, pos, src, color, 0f, Vector2.Zero,
                            PixelsPerTile / 16f, SpriteEffects.None, 0f);
                    }
                }
            }
        }

        private static void DrawFly(SpriteBatch sb, FlyAgent agent, Vector2 cam, Vector2 center)
        {
            var npc = agent.Npc;
            if (npc.type >= TextureAssets.Npc.Length) return;
            var asset = TextureAssets.Npc[npc.type];
            if (asset == null) return;
            Texture2D sheet = asset.Value;
            if (sheet == null) return;

            int frames = Math.Max(1, Main.npcFrameCount[(int)npc.type]);
            int frameH = sheet.Height / frames;
            var src = new Rectangle(0, Math.Clamp((int)npc.frame.Y, 0, sheet.Height - frameH),
                sheet.Width, frameH);
            var pos = ToScreen(npc.Center, cam, center);
            float rot = npc.rotation + (npc.spriteDirection < 0 ? MathHelper.Pi : 0f);
            float scale = PixelsPerTile / 16f * 1.8f;

            sb.Draw(sheet, pos, src, Color.White, rot,
                new Vector2(sheet.Width * 0.5f, frameH * 0.5f), scale, SpriteEffects.None, 0f);
        }

        private static void DrawFliesAndPlayers(SpriteBatch sb, FlyAgent agent, Vector2 cam, Vector2 center)
        {
            // other NPCs nearby, so the fly's world does not look empty
            for (int i = 0; i < Main.maxNPCs; i++)
            {
                NPC npc = Main.npc[i];
                if (!npc.active || npc == agent.Npc) continue;
                if (Vector2.DistanceSquared(npc.Center, agent.Npc.Center) > 60f * 16f * (60f * 16f)) continue;
                if (npc.type >= TextureAssets.Npc.Length) continue;
                var asset = TextureAssets.Npc[npc.type];
                if (asset == null) continue;
                Texture2D sheet = asset.Value;
                if (sheet == null) continue;
                int frames = Math.Max(1, Main.npcFrameCount[(int)npc.type]);
                int frameH = sheet.Height / frames;
                var src = new Rectangle(0, Math.Clamp((int)npc.frame.Y, 0, sheet.Height - frameH),
                    sheet.Width, frameH);
                sb.Draw(sheet, ToScreen(npc.Center, cam, center), src, Color.White, npc.rotation,
                    new Vector2(sheet.Width * 0.5f, frameH * 0.5f),
                    PixelsPerTile / 16f * npc.scale, SpriteEffects.None, 0f);
            }

            for (int i = 0; i < Main.maxPlayers; i++)
            {
                Player p = Main.player[i];
                if (p == null || !p.active) continue;
                if (Vector2.DistanceSquared(p.Center, agent.Npc.Center) > 60f * 16f * (60f * 16f)) continue;
                var pos = ToScreen(p.Center, cam, center);
            }
        }

        private static Vector2 ToScreen(Vector2 world, Vector2 cam, Vector2 center)
        {
            return new Vector2(
                center.X + (world.X - cam.X) / 16f * PixelsPerTile,
                center.Y + (world.Y - cam.Y) / 16f * PixelsPerTile);
        }
    }
}

