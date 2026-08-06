import unittest

from tools.gba.task8_trace import parse_trace_lines, summarize_experiment


class Task8TraceTests(unittest.TestCase):
    def test_parses_machine_readable_event(self):
        events = parse_trace_lines(
            [
                "noise from gdb\n",
                "TASK8|experiment=name-entry|event=breakpoint|pc=0x080665a2|r0=0x02001000|length=12\n",
            ]
        )
        self.assertEqual(
            events,
            [
                {
                    "experiment": "name-entry",
                    "event": "breakpoint",
                    "pc": 0x080665A2,
                    "r0": 0x02001000,
                    "length": 12,
                }
            ],
        )

    def test_parses_memory_and_boolean_fields(self):
        events = parse_trace_lines(
            [
                "TASK8|experiment=eeprom-tail|event=block|block=0x3ef|write=true|data=001122aaff\n"
            ]
        )
        self.assertEqual(events[0]["block"], 0x3EF)
        self.assertIs(events[0]["write"], True)
        self.assertEqual(events[0]["data"], "001122aaff")

    def test_rejects_duplicate_and_malformed_fields(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_trace_lines(["TASK8|event=a|event=b\n"])
        with self.assertRaisesRegex(ValueError, "key=value"):
            parse_trace_lines(["TASK8|bad\n"])

    def test_summary_reports_no_hit_without_promoting_confidence(self):
        summary = summarize_experiment("blank-core", [])
        self.assertEqual(summary["status"], "not_triggered")
        self.assertEqual(summary["confidence"], "unknown")
        self.assertEqual(summary["events"], [])

    def test_summary_keeps_executed_events(self):
        events = parse_trace_lines(
            ["TASK8|experiment=new-game|event=breakpoint|pc=0x08064e10\n"]
        )
        summary = summarize_experiment("new-game", events)
        self.assertEqual(summary["status"], "executed")
        self.assertEqual(summary["confidence"], "runtime_observed")
        self.assertEqual(summary["event_count"], 1)


if __name__ == "__main__":
    unittest.main()
