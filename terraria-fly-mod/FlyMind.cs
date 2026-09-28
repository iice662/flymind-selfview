using System;
using System.IO;
using FlyMind.Neural;
using Terraria.ModLoader;

namespace FlyMind
{
    /// <summary>
    /// "FlyMind" - a Drosophila brain model (MaleCNS v1.0 connectome,
    /// Shiu et al. 2024 leaky integrate-and-fire dynamics) driving fruit flies
    /// in Terraria.
    ///
    /// The circuit blob (flymind.brain) is produced offline by tools/CircuitBuilder
    /// from the published connectivity + annotation + transmitter data.
    /// Search order for the blob:
    ///   1. $FLYMIND_BRAIN (environment variable, absolute path)
    ///   2. next to the packed .tmod in the Mods folder
    ///   3. &lt;mod sources&gt;/FlyMind/Assets/flymind.brain
    ///   4. D:\projects\science\flymind.brain   (this machine's build output)
    /// </summary>
    public class FlyMind : Mod
    {
        public static FlyMind Instance { get; private set; }

        /// <summary>Shared circuit structure loaded from the blob (read-only).</summary>
        public BrainData CircuitData { get; private set; }

        public bool BrainAvailable => CircuitData != null;

        /// <summary>F7: show/hide the neuro lab panel (see UI.NeuroLabHud).</summary>
        public static ModKeybind ToggleLab { get; private set; }

        /// <summary>F8: write a snapshot of the current reading to flymind_neurolab.txt.</summary>
        public static ModKeybind DumpSnapshot { get; private set; }

        /// <summary>F9 - run the self-observation experiment (World/CxExperiment).</summary>
        public static ModKeybind ToggleExperiment { get; private set; }

        public override void Load()
        {
            Instance = this;
            ToggleLab = KeybindLoader.RegisterKeybind(this, "NeuroLabToggle", "F7");
            DumpSnapshot = KeybindLoader.RegisterKeybind(this, "NeuroLabSnapshot", "F8");
            ToggleExperiment = KeybindLoader.RegisterKeybind(this, "SelfViewExperiment", "F9");

            string env = Environment.GetEnvironmentVariable("FLYMIND_BRAIN");
            string modsFolder = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                "My Games", "Terraria", "tModLoader", "Mods");
            string[] candidates = {
                env,
                // next to the packed .tmod: the 16 MB circuit blob is shipped as a plain
                // file rather than packed, so it lives beside the mod in the Mods folder
                Path.Combine(ModLoader.ModPath, "flymind.brain"),
                Path.Combine(modsFolder, "flymind.brain"),
                Path.Combine(ModLoader.ModPath, "..", "ModSources", "FlyMind", "Assets", "flymind.brain"),
                @"D:\projects\science\flymind.brain",
            };

            foreach (string raw in candidates)
            {
                if (string.IsNullOrWhiteSpace(raw)) continue;
                string path;
                try { path = Path.GetFullPath(raw); }
                catch (Exception) { continue; }
                if (!File.Exists(path)) continue;

                try
                {
                    CircuitData = BrainData.Load(path);
                    Logger.InfoFormat(
                        "FlyMind: brain loaded from {0} - {1} neurons, {2} synapses, {3} sugar / {4} odor seeds",
                        path, CircuitData.NeuronCount, CircuitData.SynapseCount,
                        CircuitData.SugarSeeds.Length, CircuitData.OdorSeeds.Length);
                    break;
                }
                catch (Exception e)
                {
                    Logger.WarnFormat("FlyMind: failed to load {0}: {1}", path, e.Message);
                }
            }

            // Fallback: the packed copy inside the .tmod.  The external file beside the mod
            // is the source of truth (it can be swapped without repacking, which is how the
            // circuit gets rebuilt), but a fresh install with only the .tmod should still
            // find a brain.
            if (CircuitData == null)
            {
                try
                {
                    byte[] packed = GetFileBytes("Assets/flymind.brain");
                    if (packed != null && packed.Length > 0)
                    {
                        string tmp = Path.Combine(Path.GetTempPath(), "flymind.brain");
                        File.WriteAllBytes(tmp, packed);
                        CircuitData = BrainData.Load(tmp);
                        Logger.InfoFormat("FlyMind: brain loaded from the packed asset "
                                          + "({0} neurons, {1} synapses)",
                                          CircuitData.NeuronCount, CircuitData.SynapseCount);
                    }
                }
                catch (Exception e)
                {
                    Logger.Warn("FlyMind: no packed asset either: " + e.Message);
                }
            }

            if (CircuitData == null)
                Logger.Warn("FlyMind: no flymind.brain found - flies fall back to scripted behaviour. " +
                            "Rebuild it with tools/CircuitBuilder and drop it into the Mods folder.");
        }

        public override void Unload()
        {
            // The eye view owns a RenderTarget2D and a SpriteBatch in static fields, so a
            // mod reload (or returning to the menu) has to release them explicitly -
            // otherwise the next load reuses graphics resources from a dead device and can
            // take the game down on the first frame it renders.
            Vision.FlyEyeView.Dispose();
            ToggleLab = null;
            DumpSnapshot = null;
            ToggleExperiment = null;
            CircuitData = null;
            Instance = null;
        }
    }
}
