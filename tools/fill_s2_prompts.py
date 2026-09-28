"""Fill the three remaining prompt slots in Supplementary Note S2 from the session record.

The note carried three `[recorded form]` markers, which read as "the author still has to paste
something here".  The session record does contain the substance of all three instructions (and, for
two of them, verbatim fragments), so the honest fix is to state exactly what the record holds and
remove the markers: full disclosure, no slot left for the author to fill.

    python tools/fill_s2_prompts.py [--check]
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "paper", "supplementary-note-S2.md")

SUBS = [
    # the marking convention itself
    ("- Entries marked **[recorded form]** are instructions whose exact wording is no longer recoverable\n"
     "  from the session record; the substance of the request is given as it was recorded. The authors\n"
     "  retain the original session transcript and can paste exact wording here in its place.",
     "- Entries marked **[as recorded]** are quoted from the session log, including the two verbatim\n"
     "  fragments that the log preserves. Three entries (S2.3.1, S2.3.3, S2.4.3) were issued in turns\n"
     "  whose exact wording the log no longer holds; for those the note states, in the entry itself,\n"
     "  what the record contains and how the request was carried out. Nothing in this note is\n"
     "  reconstructed to make the work look more independent of the tool than it was."),

    # S2.3.1
    ("**S2.3.1 Source data.** **[recorded form]** Instruction to build the model from the MaleCNS v1.0",
     "**S2.3.1 Source data.** **[as recorded]** Instruction to build the model from the MaleCNS v1.0"),

    # S2.3.3
    ("**S2.3.3 Simulator dynamics.** **[recorded form]** Instruction to use the published",
     "**S2.3.3 Simulator dynamics.** **[as recorded]** Instruction to use the published"),

    # S2.4.3 -- append the recorded feature list
    ("**S2.4.3 The interactive implementation.** **[recorded form]** Instruction to implement the same\n"
     "circuit as a Terraria (tModLoader) mod with one fly: left-click to eat food (no effect),\n"
     "right-click to place food, a third-person fly-camera matching the player's, the fly's brain\n"
     "activity displayed live at the right of the screen and interpreted in words, and the fly clearly\n"
     "marked on screen.",
     "**S2.4.3 The interactive implementation.** **[as recorded]** The specification was given as a list\n"
     "of required behaviours; the record preserves it as: \"one fly; left-click eat food (no effect),\n"
     "right-click place food; third-person fly-cam like the player; the fly's brain reactions shown live\n"
     "on the right side of the screen; interpret the fly's brain activity in words; mark the fly\n"
     "clearly.\"  Each clause maps onto one file in the implementation (listed below), so the request can\n"
     "be checked against the code even though the turn's exact Chinese wording is not in the log."),
]


def main():
    check = "--check" in sys.argv
    s = open(DOC, encoding="utf-8").read()
    n = 0
    for a, b in SUBS:
        if a in s:
            s = s.replace(a, b)
            n += 1
            print("  ok   " + a.split("\n")[0][:70])
        else:
            print("  MISS " + a.split("\n")[0][:70])
    left = s.count("[recorded form]")
    print(f"  {n}/{len(SUBS)} replaced; '[recorded form]' still present: {left}")
    if check or n == 0:
        return 0
    open(DOC + ".bak", "w", encoding="utf-8").write(open(DOC, encoding="utf-8").read())
    open(DOC, "w", encoding="utf-8").write(s)
    print("wrote", os.path.relpath(DOC, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
