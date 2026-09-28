using FlyMind.Neural;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace FlyMind.Items
{
    /// <summary>
    /// "Fly Food" - a lump of over-ripe fruit that every Drosophila in the world
    /// can smell.
    ///
    /// Left click  : the player eats it. Nothing happens (it is fly food).
    /// Right click : places it in the world; nearby flies smell it through their
    ///               real olfactory circuit and get a dopamine hit.
    /// </summary>
    public class FlyFood : ModItem
    {
        public override void SetStaticDefaults()
        {
            // left click = use, right click = place
            ItemID.Sets.ItemsThatAllowRepeatedRightClick[Type] = true;
        }

        public override void SetDefaults()
        {
            Item.width = 20;
            Item.height = 20;
            Item.maxStack = 99;
            Item.useStyle = ItemUseStyleID.EatFood;
            Item.useAnimation = 20;
            Item.useTime = 20;
            Item.UseSound = SoundID.Item2;
            Item.consumable = false;   // it is not food for you, and it never runs out
            Item.rare = ItemRarityID.Blue;
            Item.value = 0;
        }

        public override bool AltFunctionUse(Player player) => true;

        public override bool CanRightClick() => true;

        public override void RightClick(Player player)
        {
            // Right click places a food patch at the cursor, if the ground is free.
            Vector2 target = Main.MouseWorld;
            if (!WorldGen.InWorld((int)(target.X / 16f), (int)(target.Y / 16f)))
                return;

            FoodScentSystem.PlacePatch(target, player);
            Main.NewText("你把果泥按在了地上。", 200, 180, 120);
        }

        public override bool? UseItem(Player player)
        {
            if (player.altFunctionUse == 2)
                return true;   // handled by RightClick

            // Left click: eating it does absolutely nothing. That is the joke.
            if (player.itemAnimation == player.itemAnimationMax - 1)
            {
                Main.NewText("你尝了一口。你的舌头不是感器。", 190, 150, 150);
            }
            return true;
        }

        public override void AddRecipes()
        {
            CreateRecipe()
                .AddIngredient(ItemID.Mushroom)
                .AddIngredient(ItemID.Bottle)
                .AddTile(TileID.WorkBenches)
                .Register();
        }
    }
}
