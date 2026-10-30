import unittest
from daze_telemetry.telemetry import SampleIRSDK, build_snapshot, empty_snapshot, flag_label, CHECKERED, RED, CAUTION, GREEN


class TestSnapshot(unittest.TestCase):
    def test_demo_positions_and_focus(self):
        ir = SampleIRSDK()
        result = build_snapshot(ir, demo=True, now=1234)
        self.assertTrue(result['connected'])
        self.assertTrue(result['demo'])
        self.assertEqual(result['session']['lap_text'], 'LAP 16 / 45')
        self.assertEqual(result['session']['flag'], 'green')
        self.assertEqual(len(result['leaderboard']), 12)
        self.assertEqual(result['leaderboard'][0]['position'], 1)
        self.assertEqual(result['focus']['idx'], 2)
        self.assertEqual(result['driver']['idx'], 3)
        self.assertEqual(result['table_type'], 'running_order')
        self.assertEqual(result['updated_at'], 1234)

    def test_offline_never_carries_old_data(self):
        result = empty_snapshot()
        self.assertFalse(result['connected'])
        self.assertEqual(result['leaderboard'], [])
        self.assertIsNone(result['focus'])
        self.assertEqual(result['session'], {})

    def test_missing_positions_do_not_invent_standings(self):
        ir = SampleIRSDK()
        ir.data['CarIdxPosition'] = [0] * 12
        ir.data['CarIdxBestLapTime'] = [0] * 12
        result = build_snapshot(ir)
        self.assertEqual(result['leaderboard'], [])
        self.assertIsNone(result['table_type'])
        self.assertIsNone(result['driver']['position'])

    def test_practice_uses_best_lap_not_race_position(self):
        ir = SampleIRSDK()
        ir.data['SessionInfo']['Sessions'][0]['SessionType'] = 'Practice'
        ir.data['CarIdxPosition'] = [0] * 12
        result = build_snapshot(ir)
        self.assertEqual(result['table_type'], 'fastest_laps')
        self.assertEqual(result['leaderboard'][0]['name'], 'Alex Morgan')
        self.assertIsNone(result['focus']['position'])
        self.assertIsNone(result['driver']['position'])

    def test_pace_and_spectator_cars_are_filtered(self):
        ir = SampleIRSDK()
        ir.data['DriverInfo']['Drivers'][1]['CarIsPaceCar'] = True
        ir.data['DriverInfo']['Drivers'][2]['IsSpectator'] = True
        result = build_snapshot(ir)
        self.assertEqual(len(result['leaderboard']), 10)
        self.assertEqual(result['focus']['idx'], 3)  # fallback to actual driver

    def test_flags_have_expected_priority(self):
        self.assertEqual(flag_label(GREEN | CAUTION), 'yellow')
        self.assertEqual(flag_label(CHECKERED | CAUTION), 'checkered')
        self.assertEqual(flag_label(RED | GREEN), 'red')
        self.assertIsNone(flag_label(None))

    def test_minimal_telemetry_does_not_crash(self):
        class EmptySDK:
            def __getitem__(self, name):
                raise KeyError(name)
        out = build_snapshot(EmptySDK())
        self.assertEqual(out['leaderboard'], [])
        self.assertIsNone(out['focus'])
        self.assertIsNone(out['session']['lap_text'])

    def test_session_label_no_unknown_placeholder(self):
        ir = SampleIRSDK()
        ir.data['WeekendInfo'] = {}
        ir.data['SessionInfo'] = {}
        result = build_snapshot(ir)
        self.assertIsNone(result['session']['track'])
        self.assertIsNone(result['session']['kind'])
        self.assertNotIn('TBA', str(result))


if __name__ == '__main__':
    unittest.main()
