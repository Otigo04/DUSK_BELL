namespace Nightward.Opening
{
    /// <summary>
    /// Texte der Ankunft im Dorf (Level_01) und der ersten Begegnung mit Sheriff Bulut in der Station.
    /// Die Station-Szene ist 1:1 aus "Nightward - Sheriff Bulut: Erste Begegnung (Ink)" (Scene 1, Oct 21, 2026) bis "Go now. Ilhan is waiting."
    /// uebernommen, die Verzweigungen stehen als Ablauf im ArrivalDirector. Die Ankunftstexte davor sind aus dem alten Opening
    /// (OpeningScript) auf den neuen Friedhof am Dorfeingang umgeschrieben. Der Weg zur Bar und die Nacht folgen spaeter.
    /// </summary>
    public static class ArrivalScript
    {
        const float Quick = 0.45f;   // kurze Atempause fuer Folgezeilen derselben Rede

        static Line B(string expr, string text, float pause = Quick) =>
            new Line { speaker = "Bulut", expr = expr, text = text, pause = pause, mumble = true };

        public const string QuestFollow = "Follow Bulut to the station";
        public const string QuestBar = "Go to the bar and talk to Ilhan";

        // ------------------------------------------------------------ Ankunft am Friedhof

        public static readonly Line[] GraveEntry =
        {
            Line.N("The village begins with a graveyard. People in dark clothes stand around a freshly dug grave. A body lies wrapped in white linen beside an empty coffin. Nobody speaks as the car passes. Their heads turn slowly with it."),
            Line.N("A woman presses a cloth to her mouth. A boy points at the car and is pulled back by his mother."),
            Line.T("What is this place?"),
            Line.T("Why are they all looking at me?"),
        };

        public static readonly string[] Whispers =
        {
            "Another one...",
            "Don't look at the car.",
            "Not again. Not so soon.",
            "Poor soul. Doesn't know yet.",
        };
        public const string MotherCall = "Come here. Now.";

        // Bulut am Autofenster (aus Opening Scene 3, auf den Friedhof umgeschrieben). Der Spieler geht mit.
        public static readonly Line[] AtTheWindow =
        {
            Line.N("Sheriff Bulut hurries over from the graveyard and leans in at the window."),
            Line.N("Your hands won't let go of the wheel. Your heart is pounding."),
            Line.Bulut("tense", "Listen to me. Please. Don't panic."),
            Line.N("You can barely breathe. Behind him, everyone at the grave is still staring at you."),
            Line.Bulut("cold", "What happened to you happened to all of us. Nobody who arrived here understood it right away."),
            Line.N("He speaks slowly and quietly, the way you would talk to a frightened animal."),
            Line.Bulut("tense", "Everyone here has seen the log at some point. Everyone here has turned around."),
            Line.Bulut("tense", "We'll get through this together. But not out here. You have to come with me to the station. I can explain everything there."),
            Line.N("Part of you wants to slam the pedal down. Part of you wants to believe him."),
            Line.Bulut("suspicious", "Please. Trust me."),
            Line.N("You switch off the engine. Your legs feel like someone else's as you climb out."),
        };

        public static readonly Line[] WalkToStation =
        {
            Line.N("The engine ticks as it cools."),
            Line.N("Sheriff Bulut turns without a word and walks up the road toward the station. He doesn't look back."),
            Line.N("The people at the grave look away as you follow."),
        };

        // ------------------------------------------------------------ Station, Scene 1

        public static readonly Line[] Arrival =
        {
            Line.N("The station smells of old coffee and wet wool."),
            Line.N("A talisman hangs on a hook beside the door, faint blue light."),
            Line.N("Sheriff Bulut doesn't look up from his desk."),
            B("cold", "Sit down.", 1.0f),
            B("cold", "I'm sorry this is your life now.", 0.8f),
        };
        public const string ChoiceSit = "Sit down across from him.";
        public const string ChoiceStayAtDoor = "Stay by the door, near the talisman.";
        public const string ChoiceLookAround = "Look around the room first.";

        public static readonly Line[] StayAtDoor =
        {
            Line.N("You stay where you are, one hand close to the wall. The talisman glows faintly beside your shoulder."),
            Line.N("Bulut looks up for the first time. He follows your gaze to the hook."),
            B("cold", "Good. You already understand more than you think.", 0.8f),
            B("cold", "Sit down anyway. This will take a while."),
        };
        public const string ChoiceStayAndListen = "Stay by the door and listen.";

        public static readonly Line LookAround =
            Line.N("You take in the room: a village map on the wall, a shelf of old files, a handwritten list of names beside the window.");
        public static readonly Line LookAroundBulut = B("cold", "Done looking? Sit down. Those names are not for you yet.", 0.8f);
        public const string ChoiceAskList = "Ask him about the list.";

        public static readonly Line AskAboutList =
            B("tense", "Those are the people who died. Every name was once someone's neighbor.", 0.8f);

        public static readonly Line[] SitDown =
        {
            Line.N("You pull out the chair and sit across from him."),
            Line.N("Bulut finally looks up. He looks tired more than angry."),
            B("tense", "The conversation we are about to have is essential for your survival in this village.", 0.8f),
            B("tense", "Listen carefully. I'm not joking. This is life or death."),
        };

        public static readonly Line[] BulutNext =
        {
            B("tense", "You have to believe me.", 0.8f),
            B("tense", "What I say next will sound absurd to you."),
            B("tense", "But if you don't listen and follow my rules, they will brutally kill you at night."),
            Line.N("You frown and lean forward, asking without words."),
            Line.You("What is going on? Who is they? Who is trying to kill me? This makes no sense!"),
        };

        public static readonly Line[] BulutAnswers =
        {
            B("cold", "They look like us. That's the problem.", 0.8f),
            B("cold", "Smiling is how you tell."),
        };
        public const string ChoiceLeave = "Stand up and walk toward the door.";
        public const string ChoiceStayStill = "Stay still and wait.";

        public static readonly Line[] LeaveAttempt =
        {
            B("tense", "Sit back down. Outside, that door won't protect you.", 0.7f),
            Line.N("You hesitate with your hand on the door handle."),
            B("angry", "I'm not asking twice.", 0.7f),
            Line.N("You sit back down, slowly."),
        };

        public static readonly Line[] Rules =
        {
            B("cold", "Thank you for listening. Most people don't.", 0.8f),
            B("tense", "First. Be inside before the bell rings. Every night, no exceptions."),
            B("tense", "Second. Never open your door at night, not even for people you know."),
            B("tense", "Third. Don't trust anyone who smiles too wide."),
            B("tense", "They are monsters. They wear our faces and hunt us at night."),
            B("cold", "It sounds absurd, I know. But it's true."),
            B("tense", "Only the houses with a talisman are safe. Stay in one."),
            B("cold", "Many people have died."),
        };

        public static readonly Line[] Reaction =
        {
            Line.N("You fold your hands and say nothing."),
            B("cold", "I came in off that same road. I didn't believe a word of it either.", 0.8f),
            Line.You("How long have you been here?"),
            B("cold", "Long enough to know the rules. Not long enough to know why.", 0.8f),
            Line.You("How do you get out of here? That obviously can't be real."),
            B("tense", "Physics and reason stopped applying the day you arrived. Learn the rules instead.", 0.8f),
            B("tense", "Sticking to the rules will assure your survival and the survival of the village."),
            Line.You("Who made the rules?"),
            B("cold", "The rules were learned by people dying. Our mistakes made them.", 0.8f),
            B("tense", "If we don't follow them strictly, more lives will be lost."),
            Line.N("You nod, frightened, but you believe him."),
            B("cold", "Go to the bar. Talk to Bartender Ilhan. He'll show you where you can stay tonight.", 0.8f),
            B("tense", "When you hear the bell, you must be home. Secure the windows and doors."),
            B("tense", "Make sure the talisman hangs by your door. Without it, they come inside."),
            B("cold", "Go now. Ilhan is waiting."),
        };
    }
}
