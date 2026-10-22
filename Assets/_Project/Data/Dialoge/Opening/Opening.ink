// ============================================================
// DUSK BELL - Opening dialogue (Ink)
// Source of truth: Dialogue Bible and Opening Sequence (wiki)
// Status: draft v1
// #added = von Claude ergaenzte Erzaehlerzeilen (Spieler hat Angst und wird beruhigt), Absprache mit Orhan 2026-10-21.
// Im Spiel umgesetzt in Scripts/Opening/OpeningScript.cs (kein Ink-Plugin). Aenderungen dort mitziehen.
// ============================================================

// GLOBAL VARIABLES (directed: from -> to, range -10 to +10)
VAR rel_bulut_player = 0
VAR rel_ilhan_player = 0
VAR rel_veronica_player = 2
VAR rel_elenora_player = -2
VAR rel_village_player = 0
VAR rel_manor_player = 0

VAR rel_bulut_ilhan = 0
VAR rel_ilhan_bulut = 0
VAR rel_bulut_veronica = 5
VAR rel_veronica_bulut = 5
VAR rel_ilhan_veronica = -3
VAR rel_veronica_ilhan = -2
VAR rel_bulut_elenora = -2
VAR rel_elenora_bulut = 0
VAR rel_ilhan_elenora = 2
VAR rel_elenora_ilhan = 2
VAR rel_veronica_elenora = -5
VAR rel_elenora_veronica = -2
VAR rel_village_manor = -3
VAR rel_manor_village = -2
VAR has_list = false

=== function clamp(v, lo, hi) ===
~ return MAX(lo, MIN(hi, v))


// STEP 2: Black intro
=== opening_intro ===
Every road leads back. #speaker:Narrator #fade:1 #hold:3
You were on your way somewhere better. Somewhere far from here. #speaker:Narrator #fade:1 #hold:3
Then the road stopped. And the village was waiting. #speaker:Narrator #fade:1 #hold:3
Night comes early in Dusk Bell. And it never comes alone. #speaker:Narrator #fade:1 #hold:3
-> END


// STEP 4: Log trigger
=== road_log_stop ===
The radio dies into static. The birds fall silent. #speaker:Narrator
-> END


// STEP 7: Investigate the log (prop, not dialogue)
=== log_found ===
~ has_list = true
You found: a torn list of names. #speaker:Narrator
// PROP CONTENT (draft):
//   Names with dates, handwritten.
//   First entry: Veronica's husband, dated the first night.
//   Last entry: the person buried in the square, dated the night before the player arrived.
-> END


// STEP 9: Village entrance (funeral)
=== village_entry ===
The square is full of people in dark clothes, standing around a freshly dug grave. Nobody speaks as the car passes. Their heads turn slowly with it. #speaker:Narrator
A woman presses a cloth to her mouth. A boy points at the car and is pulled back by his mother. #speaker:Narrator
What is this place? #speaker:Narrator #thought
Why are they all looking at me? #speaker:Narrator #thought
-> END


// STEP 10 and 11: Scene 3, Bulut at the window
=== scene3_bulut_window ===
Sheriff Bulut runs over from the square and leans in at the window. #speaker:Narrator
Your hands won't let go of the wheel. Your heart is pounding. #speaker:Narrator #added
Listen to me. Please. Don't panic. #speaker:Bulut #expr:tense #voice:mumble #pause:1.5
You can barely breathe. Behind him, the whole square is still staring at you. #speaker:Narrator #added
What happened to you happened to all of us. Nobody who arrived here understood it right away. #speaker:Bulut #expr:cold #voice:mumble #pause:1.5
He speaks slowly and quietly, the way you would talk to a frightened animal. #speaker:Narrator #added
Everyone here has seen the log at some point. Everyone here has turned around. #speaker:Bulut #expr:tense #voice:mumble #pause:1.5
We'll get through this together. But not out here. You have to come with me to the station. I can explain everything there. #speaker:Bulut #expr:tense #voice:mumble #pause:1.5
Part of you wants to slam the pedal down. Part of you wants to believe him. #speaker:Narrator #added
Please. Trust me. #speaker:Bulut #expr:suspicious #voice:mumble #pause:1.5

* [Go with him.]
    ~ rel_bulut_player = clamp(rel_bulut_player + 1, -10, 10)
    -> revier_follow
* [Drive on.]
    ~ rel_bulut_player = clamp(rel_bulut_player - 1, -10, 10)
    -> cutscene_loop


// STEP 12a: Go with him (station). Written in v2.
=== revier_follow_stub ===
// Old stub, replaced by revier_follow below.
-> END


// STEP 12b: Drive on (cutscene)
=== cutscene_loop ===
The car turns. The log is gone. The road runs straight ahead. The odometer shows the same number as before. #speaker:Narrator
-> scene4_return


// SCENE 4: Return to the village
=== scene4_return ===
Dusk. The bell rings twice, heavy and metal. #speaker:Narrator
Sheriff Bulut stands under the lantern, the handbell in his hand. #speaker:Narrator
A man at his door looks at the car, then at his neighbor, then at the car again. Nobody waves. He closes the door. #speaker:Narrator
You're back. I heard you before I saw you. #speaker:Bulut #expr:cold #voice:mumble #pause:1.5
The road doesn't let anyone leave. You didn't know that. Now you do. #speaker:Bulut #expr:cold #voice:mumble #pause:1.5
Go to Ilhan. The night won't wait for you, and I can't bring everyone in. #speaker:Bulut #expr:tense #voice:mumble #pause:1.5
He rings the bell a third time. The lights in the houses go out, one by one. #speaker:Narrator
-> scene5_ilhan_bar


// SCENE 5: Ilhan in the bar
=== scene5_ilhan_bar ===
The bar door is locked. After the second knock, a bolt slides back from inside. #speaker:Narrator
Bartender Ilhan stands behind the counter. He is no longer wiping it. He lives here alone. He looks at you for a long time, without expression. #speaker:Narrator
You heard the bell. Then you know we don't have time. #speaker:Ilhan #expr:cold #voice:mumble #pause:1.5

* [Listen to him.]
    ~ rel_ilhan_player = clamp(rel_ilhan_player + 1, -10, 10)
    Sit down. And listen before you do something stupid. #speaker:Ilhan #expr:cold #voice:mumble #pause:1.5
    -> scene5_common
* [Contradict him.]
    ~ rel_ilhan_player = clamp(rel_ilhan_player - 2, -10, 10)
    You have no idea what you're talking about. #speaker:Ilhan #expr:angry #voice:mumble #pause:1.5
    Sit down. Listen, before you do something stupid. #speaker:Ilhan #expr:cold #voice:mumble #pause:1.5
    -> scene5_common

=== scene5_common ===
There are things out here you don't want to see. And people who won't let you survive. #speaker:Ilhan #expr:cold #voice:mumble #pause:1.5
He sets a glass on the counter. He doesn't push it toward you. He leaves it in the middle. #speaker:Narrator
-> END


// STEP 12a: Sheriff's station (v2)
=== revier_follow ===
You step out of the car. The engine ticks as it cools. #speaker:Narrator
Sheriff Bulut walks ahead without turning around. The people on the square look away as you pass. #speaker:Narrator
The sheriff's station is a small wooden building at the edge of the square. Inside, a single lamp burns. #speaker:Narrator
Bulut closes the door and sits down heavily behind the desk. #speaker:Narrator
-> revier_talk

=== revier_talk ===
Sit down. You look like you've been walking for days. #speaker:Bulut #expr:tense #voice:mumble #pause:1.5
You sit. Your knees are still shaking. #speaker:Narrator #added
A talisman hangs on the wall beside the door. A faint blue light moves inside it, slow, like breathing. #speaker:Narrator
Don't touch that. It's what keeps this room safe. #speaker:Bulut #expr:cold #voice:mumble #pause:1.5
His voice is calm. For the first time today, your breathing slows down a little. #speaker:Narrator #added
-> revier_choice

=== revier_choice ===
* {has_list} [Show him the list.]
    -> show_list
* [Ask what he knows about the monsters.]
    -> ask_monsters

=== show_list ===
You put the torn list on the desk. Bulut reads it without touching it. #speaker:Narrator
{ rel_bulut_player >= 5:
    This is Veronica's husband. First night. Veronica still asks me about him, every week. #speaker:Bulut #expr:tense #voice:mumble #pause:1.5
    Keep it. Don't show it to anyone in the village. Not yet. #speaker:Bulut #expr:tense #voice:mumble #pause:1.5
- else:
    Put that away. Not here. #speaker:Bulut #expr:suspicious #voice:mumble #pause:1.5
    Where did you get this? #speaker:Bulut #expr:cold #voice:mumble #pause:1.5
}
-> revier_end

=== ask_monsters ===
You ask him what he knows about the monsters. #speaker:Narrator
{ rel_bulut_player >= 5:
    They sleep during the day. Not always. When the danger gets high, they don't sleep at all. #speaker:Bulut #expr:tense #voice:mumble #pause:1.5
    At night they look like us. Same faces. Only the grin gives them away. Watch the mouths. #speaker:Bulut #expr:cold #voice:mumble #pause:1.5
- else:
    { rel_bulut_player <= -5:
        Bulut says nothing. He turns back to the window. #speaker:Narrator
    - else:
        I don't know everything. Nobody does. Stay inside after dark, and don't open the door for anyone you don't know. #speaker:Bulut #expr:tense #voice:mumble #pause:1.5
    }
}
-> revier_end

=== revier_end ===
Bulut stands and walks to the door. He stops with his hand on the frame. #speaker:Narrator
Stay in the station when the bell rings. Don't go out, whatever you hear. #speaker:Bulut #expr:tense #voice:mumble #pause:1.5
// Opening ends here. The day timer is already running from Step 5 and pauses during this dialogue.
-> END

// Doctor Veronica and Madame Elenora are not part of the opening.
// Their lines come with their own scenes (Veronica: later in the village; Elenora: day 2, invitation to the Villa).
