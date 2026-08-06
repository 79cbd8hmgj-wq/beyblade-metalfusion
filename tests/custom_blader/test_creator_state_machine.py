import unittest

from src.custom_blader.creator_menu import CreatorModel, STEPS, load_creator_options


class CreatorStateMachineTests(unittest.TestCase):
    def test_step_order_covers_tier_a_choices(self):
        self.assertEqual(
            STEPS,
            (
                "player_name",
                "bey_name",
                "avatar",
                "skin",
                "hair",
                "outfit",
                "portrait",
                "origin",
                "tendency",
                "summary",
                "confirm",
            ),
        )

    def test_forward_back_bounds_retain_prior_choices(self):
        creator = CreatorModel()
        creator.choose("player_name", "Nova")
        creator.next().next().choose("avatar_id", 2)
        creator.next().choose("skin_palette_id", 3)
        creator.back().back()
        self.assertEqual(creator.step, "bey_name")
        self.assertEqual(creator.state.player_name, "Nova")
        self.assertEqual(creator.state.avatar_id, 2)
        self.assertEqual(creator.state.hair_style_id, 2)
        self.assertEqual(creator.state.skin_palette_id, 3)
        creator.back().back()
        self.assertEqual(creator.step, "player_name")

    def test_cancel_and_restart_are_deterministic(self):
        creator = CreatorModel().choose("player_name", "Nova").next().cancel()
        self.assertEqual(creator.step, "cancelled")
        self.assertFalse(creator.active)
        creator.next().back()
        self.assertEqual(creator.step, "cancelled")
        creator.restart()
        self.assertTrue(creator.active)
        self.assertFalse(creator.cancelled)
        self.assertEqual(creator.step, "player_name")
        self.assertEqual(creator.state.player_name, "Blader")

    def test_existing_save_bypasses_creator(self):
        creator = CreatorModel(existing_save=True)
        self.assertTrue(creator.bypassed)
        self.assertFalse(creator.active)
        self.assertEqual(creator.step, "complete")
        creator.next().back().cancel()
        self.assertEqual(creator.step, "complete")

    def test_invalid_names_and_option_ids_are_sanitized(self):
        creator = CreatorModel()
        creator.choose("player_name", "")
        creator.choose("bey_name", "*invalid*")
        for field in (
            "avatar_id",
            "skin_palette_id",
            "hair_palette_id",
            "outfit_palette_id",
            "portrait_id",
            "origin_id",
            "tendency_id",
        ):
            creator.choose(field, 99)
            self.assertEqual(getattr(creator.state, field), 0, field)
        self.assertEqual(creator.state.player_name, "Blader")
        self.assertEqual(creator.state.bey_name, "invalid")

    def test_current_step_selection_and_summary_use_option_labels(self):
        creator = CreatorModel()
        creator.choose("player_name", "Nova").next()
        creator.choose("bey_name", "Comet").next()
        creator.select(2).next()
        creator.select(3).next()
        creator.select(1).next()
        creator.select(2).next()
        creator.select(2).next()
        creator.select(1).next()
        creator.select(3).next()
        self.assertEqual(creator.step, "summary")
        summary = creator.summary()
        self.assertEqual(summary["player_name"], "Nova")
        self.assertEqual(summary["bey_name"], "Comet")
        self.assertEqual(summary["avatar"], "Ace")
        self.assertEqual(summary["skin"], "Tone 4")
        self.assertEqual(summary["hair"], "Auburn")
        self.assertEqual(summary["outfit"], "Violet")
        self.assertEqual(summary["portrait"], "Ace")
        self.assertEqual(summary["origin"], "Technical Blader")
        self.assertEqual(summary["tendency"], "Balance")

    def test_confirm_requires_final_step_and_returns_independent_state(self):
        creator = CreatorModel().choose("player_name", "Nova")
        with self.assertRaisesRegex(RuntimeError, "confirm step"):
            creator.confirm()
        while creator.step != "confirm":
            creator.next()
        committed = creator.confirm()
        self.assertTrue(creator.completed)
        self.assertFalse(creator.active)
        self.assertEqual(creator.step, "complete")
        self.assertEqual(committed.player_name, "Nova")
        committed.player_name = "Changed"
        self.assertEqual(creator.state.player_name, "Nova")

    def test_option_manifest_has_stable_complete_id_sets(self):
        options = load_creator_options()
        self.assertEqual(options["schema_version"], 1)
        for category in (
            "avatars",
            "skin_palettes",
            "hair_palettes",
            "outfit_palettes",
            "portraits",
            "origins",
            "tendencies",
        ):
            entries = options[category]
            self.assertEqual([entry["id"] for entry in entries], [0, 1, 2, 3])
            self.assertTrue(all(entry["label"] for entry in entries))
            self.assertIn(options["defaults"][category], range(4))


if __name__ == "__main__":
    unittest.main()
