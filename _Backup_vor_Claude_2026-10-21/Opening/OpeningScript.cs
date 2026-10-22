namespace Nightward.Opening
{
    /// <summary>Eine Zeile aus Data/Dialoge/Opening/Opening.ink. speaker null = Erzaehler.</summary>
    public struct Line
    {
        public string speaker;   // #speaker (null = Narrator)
        public string text;
        public string expr;      // #expr
        public float pause;      // #pause, Sekunden vor der Zeile
        public bool mumble;      // #voice:mumble
        public bool thought;     // #thought (kursiv)

        public static Line N(string text) => new Line { text = text };
        public static Line T(string text) => new Line { text = text, thought = true };
        public static Line Bulut(string expr, string text) =>
            new Line { speaker = "Bulut", expr = expr, text = text, pause = 1.5f, mumble = true };
    }

    /// <summary>
    /// Texte der Opening Sequence 1:1 aus Opening.ink (Dialogue Ink, draft v1). Quelle der Wahrheit bleibt die .ink-Datei:
    /// Aendert sich dort etwas, hier mitziehen. Kein Ink-Laufzeit-Plugin noetig.
    /// </summary>
    public static class OpeningScript
    {
        // STEP 2: Black intro (#fade:1 #hold:3)
        public static readonly string[] Intro =
        {
            "Every road leads back.",
            "You were on your way somewhere better. Somewhere far from here.",
            "Then the road stopped. And the village was waiting.",
            "Night comes early in Dusk Bell. And it never comes alone.",
        };
        public const string Title = "DUSK BELL";

        // STEP 4
        public static readonly Line RoadLogStop = Line.N("The radio dies into static. The birds fall silent.");

        // STEP 7
        public const string LogFound = "You found: a torn list of names.";

        /// <summary>
        /// Inhalt des Zettels. PLATZHALTER: Namen und Daten sind noch nicht festgelegt.
        /// Erster Eintrag = Veronicas Mann (erste Nacht), letzter = die Person aus der Beerdigung (Nacht vor der Ankunft).
        /// </summary>
        public static readonly string[] ListEntries =
        {
            "Elias Marrow - 3 March",
            "Hanne Brook - 21 April",
            "Tobias Fenn - 9 June",
            "Old Margit - 30 July",
            "Jakob Reyl - 14 Sept.",
            "Anselm Dorn - 19 Oct.",
        };

        // STEP 9: Village entrance (funeral)
        public static readonly Line[] VillageEntry =
        {
            Line.N("The square is full of people in dark clothes, standing around a freshly dug grave. Nobody speaks as the car passes. Their heads turn slowly with it."),
            Line.N("A woman presses a cloth to her mouth. A boy points at the car and is pulled back by his mother."),
            Line.T("What is this place?"),
            Line.T("Why are they all looking at me?"),
        };

        // STEP 9: Fluestern der Trauergaeste (Sprechblasen). Nicht im Ink, von Claude ergaenzt, frei aenderbar.
        public static readonly string[] Whispers =
        {
            "Another one...",
            "Don't look at the car.",
            "Not again. Not so soon.",
            "Poor soul. Doesn't know yet.",
        };
        public const string MotherCall = "Come here. Now.";

        // STEP 10 and 11: Scene 3, Bulut at the window
        // Zeilen mit [+] sind ergaenzte Erzaehlerzeilen: der Spieler hat Angst und wird beruhigt (Bulut-Zeilen unveraendert aus dem Ink).
        public static readonly Line[] Scene3 =
        {
            Line.N("Sheriff Bulut runs over from the square and leans in at the window."),
            Line.N("Your hands won't let go of the wheel. Your heart is pounding."),                          // [+]
            Line.Bulut("tense", "Listen to me. Please. Don't panic."),
            Line.N("You can barely breathe. Behind him, the whole square is still staring at you."),          // [+]
            Line.Bulut("cold", "What happened to you happened to all of us. Nobody who arrived here understood it right away."),
            Line.N("He speaks slowly and quietly, the way you would talk to a frightened animal."),            // [+]
            Line.Bulut("tense", "Everyone here has seen the log at some point. Everyone here has turned around."),
            Line.Bulut("tense", "We'll get through this together. But not out here. You have to come with me to the station. I can explain everything there."),
            Line.N("Part of you wants to slam the pedal down. Part of you wants to believe him."),             // [+]
            Line.Bulut("suspicious", "Please. Trust me."),
        };
        public const string ChoiceGo = "Go with him.";
        public const string ChoiceDrive = "Drive on.";

        // STEP 12b: Drive on (cutscene)
        public static readonly Line CutsceneLoop =
            Line.N("The car turns. The log is gone. The road runs straight ahead. The odometer shows the same number as before.");

        // SCENE 4: Return to the village
        public static readonly Line[] Scene4Intro =
        {
            Line.N("Dusk. The bell rings twice, heavy and metal."),
            Line.N("Sheriff Bulut stands under the lantern, the handbell in his hand."),
            Line.N("A man at his door looks at the car, then at his neighbor, then at the car again. Nobody waves. He closes the door."),
        };
        public static readonly Line[] Scene4Bulut =
        {
            Line.Bulut("cold", "You're back. I heard you before I saw you."),
            Line.Bulut("cold", "The road doesn't let anyone leave. You didn't know that. Now you do."),
            Line.Bulut("tense", "Go to Ilhan. The night won't wait for you, and I can't bring everyone in."),
        };
        public static readonly Line Scene4End = Line.N("He rings the bell a third time. The lights in the houses go out, one by one.");

        // STEP 12a: Revier (v2)
        public static readonly Line[] RevierWalk =
        {
            Line.N("You step out of the car. The engine ticks as it cools."),
            Line.N("Sheriff Bulut walks ahead without turning around. The people on the square look away as you pass."),
        };
        public static readonly Line[] RevierInside =
        {
            Line.N("The sheriff's station is a small wooden building at the edge of the square. Inside, a single lamp burns."),
            Line.N("Bulut closes the door and sits down heavily behind the desk."),
            Line.Bulut("tense", "Sit down. You look like you've been walking for days."),
            Line.N("You sit. Your knees are still shaking."),                                                  // [+]
            Line.N("A talisman hangs on the wall beside the door. A faint blue light moves inside it, slow, like breathing."),
            Line.Bulut("cold", "Don't touch that. It's what keeps this room safe."),
            Line.N("His voice is calm. For the first time today, your breathing slows down a little."),        // [+]
        };
        public const string ChoiceShowList = "Show him the list.";
        public const string ChoiceAskMonsters = "Ask what he knows about the monsters.";

        public static readonly Line ShowListIntro = Line.N("You put the torn list on the desk. Bulut reads it without touching it.");
        public static readonly Line[] ShowListTrusted =
        {
            Line.Bulut("tense", "This is Veronica's husband. First night. Veronica still asks me about him, every week."),
            Line.Bulut("tense", "Keep it. Don't show it to anyone in the village. Not yet."),
        };
        public static readonly Line[] ShowListDistrust =
        {
            Line.Bulut("suspicious", "Put that away. Not here."),
            Line.Bulut("cold", "Where did you get this?"),
        };

        public static readonly Line AskMonstersIntro = Line.N("You ask him what he knows about the monsters.");
        public static readonly Line[] AskMonstersTrusted =
        {
            Line.Bulut("tense", "They sleep during the day. Not always. When the danger gets high, they don't sleep at all."),
            Line.Bulut("cold", "At night they look like us. Same faces. Only the grin gives them away. Watch the mouths."),
        };
        public static readonly Line[] AskMonstersHostile = { Line.N("Bulut says nothing. He turns back to the window.") };
        public static readonly Line[] AskMonstersNeutral =
        {
            Line.Bulut("tense", "I don't know everything. Nobody does. Stay inside after dark, and don't open the door for anyone you don't know."),
        };

        public static readonly Line[] RevierEnd =
        {
            Line.N("Bulut stands and walks to the door. He stops with his hand on the frame."),
            Line.Bulut("tense", "Stay in the station when the bell rings. Don't go out, whatever you hear."),
        };
    }
}
