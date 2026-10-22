namespace Nightward.Opening
{
    /// <summary>
    /// Texte der ersten Story-Szene in Level_01 nach "Sheriff Bulut: Erste Begegnung (Ink)" (Docs/_Sequences/Sheriff_Bulut_Erste_Begegnung.ink.txt):
    /// Ankunft am Friedhof, Station, Weg zur Bar, Bar am Tag, die erste Nacht (Klopfen am Fenster, beide Ausgaenge) und der Morgen.
    /// Die Verzweigungen stehen als Ablauf im ArrivalDirector. Die Ankunftstexte am Anfang sind aus dem alten Opening (OpeningScript)
    /// auf den Friedhof am Dorfeingang umgeschrieben. Der Spieler hat im Ink keinen Namen und keine feste Geschlechtsangabe:
    /// "{player_name}" und "he" sind hier durch neutrale Formulierungen ersetzt.
    /// </summary>
    public static class ArrivalScript
    {
        const float Quick = 0.45f;   // kurze Atempause fuer Folgezeilen derselben Rede

        static Line B(string expr, string text, float pause = Quick) =>
            new Line { speaker = "Bulut", expr = expr, text = text, pause = pause, mumble = true };

        static Line I(string text, float pause = Quick) =>
            new Line { speaker = "Ilhan", text = text, pause = pause, mumble = true };

        static Line Monster(string text, float pause = 0.8f) =>
            new Line { speaker = "Monster", text = text, pause = pause, mumble = true };

        public const string QuestFollow = "Follow Bulut to the station";
        public const string QuestBar = "Go to the bar and talk to Ilhan";
        public const string QuestVillagers = "Talk to the villagers";

        // ------------------------------------------------------------ Ankunft am Friedhof

        public static readonly Line[] GraveEntry =
        {
            Line.N("The village begins with a graveyard. People in dark clothes stand around a freshly dug grave while the pastor reads from a worn book. A body lies wrapped in white linen beside an empty coffin. Nobody speaks as the car passes. Their heads turn slowly with it."),
            Line.N("The baker presses a cloth to her mouth. The doctor lowers her eyes. A man in a woollen sweater stares at you through thick glasses, then looks away."),
            Line.T("What is this place?"),
            Line.T("Why are they all looking at me?"),
        };

        /// <summary>Gefluesterte Bemerkungen: Mara, Veronica, David.</summary>
        public static readonly string[] Whispers =
        {
            "Another one...",
            "Not again. Not so soon.",
            "Poor soul. Doesn't know yet.",
        };

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

        // ------------------------------------------------------------ Aufbruch zur Bar

        public static readonly Line[] LeaveStation =
        {
            Line.N("You ask him for the way to the bar."),
            B("cold", "I'll walk you there. Stay close to me.", 0.8f),
            Line.N("You nod and follow him out of the station."),
        };

        public static readonly Line[] WalkToBar =
        {
            Line.N("You walk half a step behind Bulut, eyes on the street."),
            B("tense", "Keep up. The street looks empty, but it's watching you.", 0.8f),
        };

        // ------------------------------------------------------------ Bar am Tag

        /// <summary>Bis Bulut geht ("Bulut leaves without looking back.").</summary>
        public static readonly Line[] BarEntrance =
        {
            Line.N("It is daytime, so the bar is open. Bulut pushes the door and walks in."),
            B("cold", "Meet the new one.", 0.8f),
            B("cold", "Ilhan, show them where they can stay tonight."),
            I("Another one. I'll show you the back room. Don't touch the windows.", 0.8f),
            Line.N("You nod and sit down at the bar."),
            B("tense", "I have to check on the others. Remember what I told you.", 0.8f),
            Line.N("Bulut leaves without looking back."),
        };

        public static readonly Line[] BarTalk =
        {
            Line.N("You stay at the bar with Ilhan."),
            I("He always says that. Doesn't mean he's wrong.", 0.8f),
            Line.You("What the fuck is going on here. Is it true what the Sheriff said? Is this some kind of prank? Are you all messing with me?"),
            I("I know. I know. I've been there.", 0.8f),
            I("Please believe the Sheriff. Don't make the mistakes others did."),
            I("Just stay inside today. All your questions and doubts will go away when you first see them."),
            Line.You("That can't be true."),
            I("Your face already believes it. Sit down before you fall.", 0.8f),
            Line.N("You sit down and hold your head in your hands."),
            I("Here, drink this.", 0.8f),
            Line.N("Ilhan fills a glass of water for you."),
            I("It is going to be dark soon.", 0.8f),
        };

        public static readonly Line[] BarBackRoom =
        {
            I("Come on. The back room is yours until morning.", 0.8f),
            Line.N("You follow him behind the bar through a narrow door."),
            Line.N("The back room has a cot, a small lamp, and a talisman hanging on a hook beside the door."),
            I("The bell rings at dusk. You can look around the bar. Stay away from the windows, they try to manipulate you. If you open a window or do what they say. That means you've killed us both.", 0.8f),
        };

        // ------------------------------------------------------------ Die erste Nacht

        public static readonly Line[] FirstNight =
        {
            Line.N("The bell rings at dusk. Ilhan turns off the lights behind the bar."),
            Line.N("You lock the door of the back room from inside and lie down on the cot."),
            Line.N("The bar falls quiet."),
        };

        public static readonly Line[] NightKnock =
        {
            Line.N("Three soft knocks against the window of the back room. Then again, slower."),
            Line.N("You wake up on the cot. Ilhan wakes in the other room and comes to the back window."),
            Line.N("Ilhan stops short when he sees who is standing outside."),
            Line.N("The figure looks human. Its grin is far too wide, and its teeth show in the dark."),
            Monster("Ilhan, let me in. It's cold out here."),
            I("I can't. The rules say no one comes in tonight.", 0.8f),
            Monster("Ilhan, it's me. You know my voice."),
        };
        public const string ChoiceOpenWindow = "Ilhan opens the window.";
        public const string ChoiceRefuse = "Refuse. The window stays closed.";

        public static readonly Line[] WindowOpened =
        {
            Line.N("Ilhan unlatches the window and pushes it open."),
            Line.N("The figure climbs through the window and walks toward the back room, toward you."),
            I("STOP! RUN!!!", 0.2f),
        };

        public static readonly Line[] RunToStation =
        {
            Line.N("Both of you run out of the bar, toward the sheriff's station."),
            Line.N("Bulut is already inside the station. He opens the door before you reach it."),
            B("angry", "In. Now. Don't look back.", 0.3f),
            Line.N("Bulut closes the door and locks it."),
            Line.N("The figure reaches the threshold and stops. Through the gap, it grins at you."),
            Line.N("Bulut waits without moving until it is gone."),
            B("tense", "What happened? Tell me what happened!", 0.5f),
            I("You were supposed to stay inside! Do you understand what you did?", 0.4f),
            Line.N("You stop breathing for a moment. This time, you believe all of it."),
            Line.N("You are in shock. Your hands won't stop shaking."),
            B("cold", "Ilhan, stop. That is enough for one night.", 0.6f),
            Line.N("Bulut pours a glass of water and pushes it across the desk."),
            B("cold", "Breathe. You're safe here. Tell me what you saw.", 0.8f),
            Line.You("It looked like a man. Then it smiled, and the smile was too wide. And then it turned into something... I can't get it out of my head."),
            B("tense", "That's the one they always send first. Don't fall for them. Please.", 0.8f),
            B("cold", "Enough for tonight. Ilhan, bring them to the cells. They sleep there tonight.", 0.8f),
            B("cold", "Tomorrow we talk again."),
        };

        public static readonly Line[] CellsNight =
        {
            Line.N("Ilhan leads you down to the cells and leaves you there. Upstairs, you hear him and Bulut talking in low voices."),
            Line.N("You are alone. You lie down on the bunk and fall asleep."),
        };

        public static readonly Line[] WindowRefused =
        {
            Line.N("You step back from the glass. The window stays closed."),
            Line.You("No, you have to ask Bartender Ilhan! He owns the bar."),
            Line.N("The figure stops grinning. It knocks on the glass again, harder, and then again."),
            Line.N("The knocking turns into pounding. The figure's voice sounds angry now."),
            Line.N("Ilhan comes in from the other room and pulls you away from the window into the hallway."),
            I("Don't look at it. Look at me. Only at me.", 0.5f),
            Line.N("The hammering stops. The street outside goes silent."),
            Line.N("Ilhan keeps you in the hallway, sitting with your back against the wall. Neither of you sleeps until morning."),
        };

        // ------------------------------------------------------------ Morgen

        /// <summary>Nach der Flucht in die Station (Zellen): Bulut wartet vor der Station.</summary>
        public static readonly Line[] MorningStation =
        {
            Line.N("It is morning. You slept through the night."),
            Line.N("Early this morning, Bulut already unlocked the cell door so you can leave."),
            Line.N("The police station is empty. There is no one left inside."),
            Line.N("You step outside. The street is empty."),
            Line.N("Bulut is standing by the station, waiting for you."),
            B("cold", "You slept. Good. Now you know the rules are real.", 0.8f),
        };

        /// <summary>Fenster blieb zu: der Morgen beginnt in der Bar, Bulut wartet vor der Tuer.</summary>
        public static readonly Line[] MorningBar =
        {
            Line.N("It is morning. The knocking stopped hours ago, and the first light finally reaches the hallway."),
            Line.N("You step outside. The street is empty."),
            Line.N("Bulut is standing in front of the bar, waiting for you."),
            B("cold", "You stayed inside. Good. Now you know the rules are real.", 0.8f),
        };

        public static readonly Line[] MorningReport =
        {
            Line.N("Bulut reads the morning report from his notebook. Nobody died in the night."),
            B("tense", "The forest sent a warning. Something moved near the trees before dawn.", 0.8f),
            B("tense", "The warning is about last night. Something stood at the bar window until dawn."),
        };
    }
}
