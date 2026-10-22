using System.Collections.Generic;
using System.IO;
using Nightward.Dialogue;
using Nightward.NPC;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Baut die neue Besetzung (Bartender Ilhan, Sheriff Bulut, Der Gast, Die Hausfrau) aus den Aseprite-Exporten:
    /// Sprites schneiden, 8-Richtungs-Controller, Profile, Dialoge, Prefabs und Testplatzierung in der Szene.
    /// Vorhandene Dialog- und Profil-Assets werden nie ueberschrieben.
    /// </summary>
    public static class NpcCastBuilder
    {
        const string CharDir = "Assets/_Project/Art/Characters/";
        const string AnimDir = "Assets/_Project/Art/Animations/";
        const string DataDir = "Assets/_Project/Data";
        const string PrefabDir = "Assets/_Project/Prefabs/Characters/";
        const string BasePrefab = PrefabDir + "NPC_Ilhan.prefab";

        // Zeilenreihenfolge der Sheets (aus den Strips ermittelt): unten, unten-links, links, ... im Uhrzeigersinn
        static readonly string[] RowDirs = { "S", "SW", "W", "NW", "N", "NE", "E", "SE" };

        internal class Clip
        {
            public string state;   // Praefix im Animator, z. B. "walk"
            public string sheet;   // Pfad relativ zu CharDir
            public int cell;       // Rahmengroesse in px
            public float fps;
            public bool loop;
            public Clip(string state, string sheet, int cell, float fps, bool loop) { this.state = state; this.sheet = sheet; this.cell = cell; this.fps = fps; this.loop = loop; }
        }

        [MenuItem("Nightward/NPCs/Neue Besetzung bauen und platzieren")]
        public static void BuildAll()
        {
            AssetDatabase.Refresh();
            EnsureFolder("Assets/_Project/Art", "Animations");
            EnsureFolder(DataDir, "NPCs");
            EnsureFolder(DataDir, "Dialoge");

            // ---- Ilhan, Bartender
            var ilhanCtrl = Controller("Ilhan_Bartender", new[]
            {
                new Clip("idle", "ILHAN BARTENDER/ANIMATIONS_8DIR/ilhan_idle_fixed.png", 56, 6, true),
                new Clip("walk", "ILHAN BARTENDER/ANIMATIONS_8DIR/ilhan_walk_fixed.png", 56, 10, true),
            });
            var ilhanProfile = Profile("ilhan_bartender", "Ilhan", "#ffa550", "ILHAN BARTENDER/portraits/ilhan_neutral.png",
                new[] { "ILHAN BARTENDER/portraits/ilhan_talk_A.png", "ILHAN BARTENDER/portraits/ilhan_talk_O.png" });
            var ilhanDialogs = IlhanDialogs();
            var ilhanPrefab = MakePrefab("NPC_Ilhan_Bartender", ilhanCtrl, null, ilhanProfile, ilhanDialogs, 2.5f, false);

            // ---- Sheriff Bulut
            var bulutCtrl = Controller("Bulut_Sheriff", new[]
            {
                new Clip("idle", "BULUT SHERIFF/ANIMATIONS_8DIR/bulut_idle_fixed.png", 56, 6, true),
                new Clip("walk", "BULUT SHERIFF/ANIMATIONS_8DIR/bulut_walk_fixed.png", 56, 10, true),
                new Clip("shoot", "BULUT SHERIFF/ANIMATIONS_8DIR/bulut_shoot_fixed.png", 72, 12, false),
            });
            var bulutProfile = Profile("bulut", "Sheriff Bulut", "#7aa8d6", "BULUT SHERIFF/portraits/bulut_calm.png",
                new[] { "BULUT SHERIFF/portraits/bulut_talk_A.png", "BULUT SHERIFF/portraits/bulut_talk_O.png" });
            var bulutPrefab = MakePrefab("NPC_Bulut_Sheriff", bulutCtrl, null, bulutProfile, BulutDialogs(), 2.5f, false);

            // ---- Der Gast (Monster)
            var gastDis = Controller("Gast_Verkleidet", new[]
            {
                new Clip("idle", "DER GAST/ANIMATIONS_8DIR/der_gast_disguised_idle_fixed.png", 56, 6, true),
                new Clip("walk", "DER GAST/ANIMATIONS_8DIR/der_gast_disguised_walk_fixed.png", 56, 10, true),
            });
            var gastRev = Controller("Gast_Enthuellt", new[]
            {
                new Clip("idle", "DER GAST/ANIMATIONS_8DIR/der_gast_revealed_idle_fixed.png", 56, 6, true),
                new Clip("walk", "DER GAST/ANIMATIONS_8DIR/der_gast_revealed_walk_fixed.png", 56, 10, true),
                new Clip("attack", "DER GAST/ANIMATIONS_8DIR/der_gast_revealed_attack_fixed.png", 72, 12, false),
            });
            var gastProfile = Profile("der_gast", "Der Gast", "#c9b79c", "DER GAST/portraits/der_gast_calm.png",
                new[] { "DER GAST/portraits/der_gast_talk_A.png", "DER GAST/portraits/der_gast_talk_O.png" });
            var gastPrefab = MakePrefab("NPC_Gast", gastDis, gastRev, gastProfile, GastDialogs(), 2.2f, true);

            // ---- Die Hausfrau (Monster)
            var hfDis = Controller("Hausfrau_Verkleidet", new[]
            {
                new Clip("idle", "DIE HAUSFRAU/ANIMATIONS_8DIR/die_hausfrau_disguised_idle_fixed.png", 56, 6, true),
                new Clip("walk", "DIE HAUSFRAU/ANIMATIONS_8DIR/die_hausfrau_disguised_walk_fixed.png", 56, 10, true),
            });
            var hfRev = Controller("Hausfrau_Enthuellt", new[]
            {
                new Clip("idle", "DIE HAUSFRAU/ANIMATIONS_8DIR/die_hausfrau_revealed_idle_fixed.png", 56, 6, true),
                new Clip("walk", "DIE HAUSFRAU/ANIMATIONS_8DIR/die_hausfrau_revealed_walk_fixed.png", 56, 10, true),
                new Clip("attack", "DIE HAUSFRAU/ANIMATIONS_8DIR/die_hausfrau_revealed_attack_fixed.png", 72, 12, false),
            });
            var hfProfile = Profile("die_hausfrau", "Die Hausfrau", "#b8a07a", "DIE HAUSFRAU/portraits/die_hausfrau_calm.png",
                new[] { "DIE HAUSFRAU/portraits/die_hausfrau_talk_A.png", "DIE HAUSFRAU/portraits/die_hausfrau_talk_O.png" });
            var hfPrefab = MakePrefab("NPC_Hausfrau", hfDis, hfRev, hfProfile, HausfrauDialogs(), 2.0f, true);

            AssetDatabase.SaveAssets();

            // ---- Testplatzierung neben dem Spieler
            var player = GameObject.Find("Player");
            Vector3 origin = player != null ? player.transform.position : Vector3.zero;
            Place(ilhanPrefab, origin + new Vector3(3f, 0f, 0f));
            Place(bulutPrefab, origin + new Vector3(5f, 0f, 0f));
            Place(gastPrefab, origin + new Vector3(7f, 0f, 0f));
            Place(hfPrefab, origin + new Vector3(9f, 0f, 0f));
            EditorSceneManager.MarkSceneDirty(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
            Debug.Log("[NPCs] Besetzung gebaut und platziert.");
        }

        /// <summary>
        /// Doctor Veronica einzeln bauen (ohne die uebrige Besetzung anzufassen): Controller mit idle/walk/run/treat in 8 Richtungen,
        /// Profil (+2 Startbeziehung), Dialoge, Prefab und Testplatzierung. Vorhandene Dialog- und Profil-Assets bleiben erhalten.
        /// </summary>
        [MenuItem("Nightward/NPCs/Doctor Veronica bauen und platzieren")]
        public static void BuildVeronica()
        {
            AssetDatabase.Refresh();
            EnsureFolder("Assets/_Project/Art", "Animations");
            EnsureFolder(DataDir, "NPCs");
            EnsureFolder(DataDir, "Dialoge");

            const string anim = "DOCTOR VERONICA/ANIMATIONS_8DIR/doctor_veronica_";
            var ctrl = Controller("Veronica_Doctor", new[]
            {
                new Clip("idle", anim + "idle_sheet.png", 56, 6, true),
                new Clip("walk", anim + "walk_sheet.png", 56, 10, true),
                new Clip("run", anim + "run_sheet.png", 56, 14, true),
                new Clip("treat", anim + "treat_sheet.png", 56, 8, true),
            });

            const string por = "DOCTOR VERONICA/portraits/veronica_";
            var profile = Profile("veronica", "Doctor Veronica", "#b89a72", por + "calm.png",
                new[] { por + "talk_A.png", por + "talk_O.png" });
            profile.gender = NpcGender.Weiblich;
            profile.startRelationship = 2;
            profile.portraitBlink = Portrait(por + "blink.png");
            // Ausdrucksbilder (Mitfuehlend, Traurig, Entschlossen) als Sprites importieren, fuer PortraitAnimator.SetExpression
            foreach (var expr in new[] { "compassionate", "sad", "determined", "talk_E" }) Portrait(por + expr + ".png");
            EditorUtility.SetDirty(profile);

            var prefab = MakePrefab("NPC_Veronica_Doctor", ctrl, null, profile, VeronicaDialogs(), 1.5f, false);
            AssetDatabase.SaveAssets();

            var player = GameObject.Find("Player");
            Vector3 origin = player != null ? player.transform.position : Vector3.zero;
            Place(prefab, origin + new Vector3(11f, 0f, 0f));
            EditorSceneManager.MarkSceneDirty(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
            Debug.Log("[NPCs] Doctor Veronica gebaut und platziert.");
        }

        static List<DialogueEntry> VeronicaDialogs()
        {
            // Platzhaltertexte nach der NPC-Doku (Kernzeilen sind dort noch offen): warm, mit aerztlichen Fachwoertern
            var kennen = Dialog("Veronica_Doctor", "Dialog_Veronica_Kennenlernen",
                N("start", Speaker.Npc, "Du bist neu hier. Komm, setz dich kurz. Hast du dich verletzt? Schürfwunde, Kopfschmerz, Schock: Ich behandle, was man mir zeigt.", null, 0, "veronica_kennengelernt",
                    C("Mir geht es gut, danke.", "gut", 1),
                    C("Was ist das für ein Schlüsselbund?", "schluessel"),
                    C("Wie lange sind Sie schon hier?", "lange")),
                N("gut", Speaker.Npc, "Das sagen alle in der ersten Nacht. Trink genug, ruh dich aus, solange es still ist. Und komm zu mir, bevor aus einem Kratzer etwas Ernstes wird."),
                N("schluessel", Speaker.Npc, "Die Praxis und der Medikamentenschrank. Beides öffnet nur dieser Bund. Ich trage ihn Tag und Nacht."),
                N("lange", Speaker.Npc, "Acht Jahre. So lange wie der Sheriff. Man gewöhnt sich nicht daran, aber man lernt, ruhig zu bleiben. Das ist die beste Medizin, die ich habe."));
            var alltag = Dialog("Veronica_Doctor", "Dialog_Veronica_Alltag",
                N("start", Speaker.Npc, "Guten Tag. Wie fühlst du dich? Schlaf, Appetit, Puls: alles in Ordnung?", null, 0, null,
                    C("Alles gut.", "gut"),
                    C("Ich bin erschöpft.", "erschoepft", 1),
                    C("Haben Sie Medikamente?", "med")),
                N("gut", Speaker.Npc, "Schön. Wenn sich das ändert, kommst du zu mir. Es fängt immer mit den kleinen Dingen an."),
                N("erschoepft", Speaker.Npc, "Das ist normal. Der Körper rechnet mit jeder Nacht. Ruh dich aus, solange es hell ist."),
                N("med", Speaker.Npc, "Der Schrank bleibt abgeschlossen. Nicht aus Misstrauen: Es ist wenig da, und es muss für alle reichen."));
            return new List<DialogueEntry>
            {
                new DialogueEntry { dialogue = kennen, onlyOnce = true },
                new DialogueEntry { dialogue = alltag },
            };
        }

        /// <summary>
        /// Baker Mara einzeln bauen: Controller mit idle/walk/run/bake (Teig kneten an der Theke) in 8 Richtungen, Profil,
        /// Dialoge, Prefab und Testplatzierung. Vorhandene Dialog- und Profil-Assets bleiben erhalten.
        /// </summary>
        [MenuItem("Nightward/NPCs/Baker Mara bauen und platzieren")]
        public static void BuildMara()
        {
            AssetDatabase.Refresh();
            EnsureFolder("Assets/_Project/Art", "Animations");
            EnsureFolder(DataDir, "NPCs");
            EnsureFolder(DataDir, "Dialoge");

            const string anim = "BAKER MARA/ANIMATIONS_8DIR/baker_mara_";
            var ctrl = Controller("Mara_Baker", new[]
            {
                new Clip("idle", anim + "idle_sheet.png", 56, 6, true),
                new Clip("walk", anim + "walk_sheet.png", 56, 10, true),
                new Clip("run", anim + "run_sheet.png", 56, 14, true),
                new Clip("bake", anim + "bake_sheet.png", 56, 8, true),
            });

            const string por = "BAKER MARA/portraits/mara_";
            var profile = Profile("mara", "Baker Mara", "#9c7a5a", por + "calm.png",
                new[] { por + "talk_A.png", por + "talk_O.png" });
            profile.gender = NpcGender.Weiblich;
            profile.startRelationship = 0;
            profile.portraitBlink = Portrait(por + "blink.png");
            // Ausdrucksbilder (Warm = Mitfuehlend, Misstrauisch, Veraengstigt) als Sprites importieren, fuer PortraitAnimator.SetExpression
            foreach (var expr in new[] { "compassionate", "suspicious", "scared", "talk_E" }) Portrait(por + expr + ".png");
            EditorUtility.SetDirty(profile);

            var prefab = MakePrefab("NPC_Mara_Baker", ctrl, null, profile, MaraDialogs(), 1.5f, false);
            AssetDatabase.SaveAssets();

            var player = GameObject.Find("Player");
            Vector3 origin = player != null ? player.transform.position : Vector3.zero;
            Place(prefab, origin + new Vector3(13f, 0f, 0f));
            EditorSceneManager.MarkSceneDirty(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
            Debug.Log("[NPCs] Baker Mara gebaut und platziert.");
        }

        static List<DialogueEntry> MaraDialogs()
        {
            // Platzhaltertexte nach der NPC-Doku (Sprechweise und Kernzeilen sind dort noch offen): herzlich, eitel, wortkarg.
            // Harren und ihr Geheimnis bleiben unausgesprochen.
            var kennen = Dialog("Mara_Baker", "Dialog_Mara_Kennenlernen",
                N("start", Speaker.Npc, "Frisch aus dem Ofen. Nimm eins. Du siehst aus, als hättest du seit gestern nichts gegessen.", null, 0, "mara_kennengelernt",
                    C("Danke, gern.", "danke", 1),
                    C("Sie waren mal Model, oder?", "model"),
                    C("Wer hatte die Bäckerei vorher?", "harren")),
                N("danke", Speaker.Npc, "Brot hab ich immer übrig. Komm morgen früh wieder, dann ist es noch warm."),
                N("model", Speaker.Npc, "Lang her. Heute steh ich vor dem Ofen statt vor der Kamera. Der Ofen ist ehrlicher. ... Das Licht fehlt mir manchmal, zugegeben."),
                N("harren", Speaker.Npc, "Harren. Der hat hier gebacken. Er ist weg. Mehr gibt es dazu nicht.", null, 0, "mara_harren_gefragt"));
            var alltag = Dialog("Mara_Baker", "Dialog_Mara_Alltag",
                N("start", Speaker.Npc, "Der Ofen läuft seit vier. Brauchst du was?", null, 0, null,
                    C("Ein Brot, bitte.", "brot", 1),
                    C("Wie läuft die Bäckerei?", "laeuft"),
                    C("Bis später.", "tschuess")),
                N("brot", Speaker.Npc, "Hier. Noch warm. Zahl, was du kannst."),
                N("laeuft", Speaker.Npc, "Solange Mehl da ist, läuft sie. Und solange einer das Licht anmacht."),
                N("tschuess", Speaker.Npc, "Sei vor Einbruch zu Hause. Talisman neben die Tür, hörst du?"));
            return new List<DialogueEntry>
            {
                new DialogueEntry { dialogue = kennen, onlyOnce = true },
                new DialogueEntry { dialogue = alltag },
            };
        }

        /// <summary>
        /// Pastor David einzeln bauen: Controller mit idle/walk/run/pray (Betanimation) in 8 Richtungen, Profil (+3 Startbeziehung),
        /// Dialoge, Prefab und Testplatzierung. Vorhandene Dialog- und Profil-Assets bleiben erhalten.
        /// </summary>
        [MenuItem("Nightward/NPCs/Pastor David bauen und platzieren")]
        public static void BuildPastor()
        {
            AssetDatabase.Refresh();
            EnsureFolder("Assets/_Project/Art", "Animations");
            EnsureFolder(DataDir, "NPCs");
            EnsureFolder(DataDir, "Dialoge");

            const string anim = "PASTOR DAVID/ANIMATIONS_8DIR/pastor_david_";
            var ctrl = Controller("David_Pastor", new[]
            {
                new Clip("idle", anim + "idle_sheet.png", 56, 6, true),
                new Clip("walk", anim + "walk_sheet.png", 56, 10, true),
                new Clip("run", anim + "run_sheet.png", 56, 14, true),
                new Clip("pray", anim + "pray_sheet.png", 56, 4, true),
            });

            const string por = "PASTOR DAVID/portraits/david_";
            // Namensfarbe ist in der Doku offen: Blattlicht (#9ab87a) aus der Palette, kein Monster- oder bereits vergebener Ton
            var profile = Profile("david", "Pastor David", "#9ab87a", por + "calm.png",
                new[] { por + "talk_A.png", por + "talk_O.png" });
            profile.gender = NpcGender.Maennlich;
            profile.startRelationship = 3;
            profile.portraitBlink = Portrait(por + "blink.png");
            // Ausdrucksbilder (Warm = Mitfuehlend, Misstrauisch, Veraengstigt) als Sprites importieren, fuer PortraitAnimator.SetExpression
            foreach (var expr in new[] { "compassionate", "suspicious", "scared", "talk_E" }) Portrait(por + expr + ".png");
            EditorUtility.SetDirty(profile);

            var prefab = MakePrefab("NPC_David_Pastor", ctrl, null, profile, PastorDialogs(), 1.5f, false);
            AssetDatabase.SaveAssets();

            var player = GameObject.Find("Player");
            Vector3 origin = player != null ? player.transform.position : Vector3.zero;
            Place(prefab, origin + new Vector3(15f, 0f, 0f));
            EditorSceneManager.MarkSceneDirty(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
            Debug.Log("[NPCs] Pastor David gebaut und platziert.");
        }

        static List<DialogueEntry> PastorDialogs()
        {
            // Platzhaltertexte nach der NPC-Doku (Sprechweise und Kernzeilen sind dort noch offen): geduldig, zerstreut, ruhig.
            // Sein Geheimnis um Veronicas Mann bleibt unausgesprochen.
            var kennen = Dialog("David_Pastor", "Dialog_David_Kennenlernen",
                N("start", Speaker.Npc, "Ah, ein neues Gesicht. Setz dich, die Bänke sind für alle da. ... Verzeih, ich wollte eigentlich etwas holen. Was war es nur?", null, 0, "david_kennengelernt",
                    C("Ist alles in Ordnung?", "ok", 1),
                    C("Sind Sie hier der Pfarrer?", "pfarrer"),
                    C("Wie hält man das hier aus?", "aushalten")),
                N("ok", Speaker.Npc, "Ich verliere nur ab und zu den Faden. Ein Gespräch ist mir wichtiger als die Uhr."),
                N("pfarrer", Speaker.Npc, "Dem Titel nach. Ich habe Theologie studiert, bin aber nie fertig geworden. Jetzt höre ich vor allem zu. Den Leuten scheint das zu reichen."),
                N("aushalten", Speaker.Npc, "Gemeinsam. Wir essen zusammen, wir wachen zusammen. Wer allein bleibt, den holt die Nacht zuerst."));
            var alltag = Dialog("David_Pastor", "Dialog_David_Alltag",
                N("start", Speaker.Npc, "Schön, dich zu sehen. Hast du einen Moment? Ich habe die Zeit schon wieder vergessen.", null, 0, null,
                    C("Wie geht es der Gemeinde?", "gemeinde"),
                    C("Beten Sie für uns?", "beten", 1),
                    C("Ich muss weiter.", "weiter")),
                N("gemeinde", Speaker.Npc, "Sie hält zusammen. Mehr wünsche ich mir nicht."),
                N("beten", Speaker.Npc, "Jeden Abend, vor der Glocke. Komm dazu, wenn du magst. Schweigen zählt auch."),
                N("weiter", Speaker.Npc, "Geh nur. Und denk an den Talisman neben der Tür."));
            return new List<DialogueEntry>
            {
                new DialogueEntry { dialogue = kennen, onlyOnce = true },
                new DialogueEntry { dialogue = alltag },
            };
        }

        // ------------------------------------------------------------------ Sprites und Animation
        static void EnsureFolder(string parent, string child)
        {
            if (!AssetDatabase.IsValidFolder(parent + "/" + child)) AssetDatabase.CreateFolder(parent, child);
        }

        /// <summary>Schneidet ein Sheet in ein festes Raster (8 Zeilen = 8 Richtungen), Pivot an den Fuessen, 32 PPU wie die Spielwelt.</summary>
        static Sprite[,] Slice(string path, int cell, out int cols)
        {
            var bytes = File.ReadAllBytes(path);
            var tex = new Texture2D(2, 2);
            tex.LoadImage(bytes);
            cols = tex.width / cell;
            const int rows = 8;

            // Fuesse liegen bei 56er-Rahmen 5 px ueber dem Rand, groessere Rahmen sind um den Rand zentriert
            float pivotY = (5f + (cell - 56) / 2f) / cell;

            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Multiple;
            ti.spritePixelsPerUnit = 32;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;

            string baseName = Path.GetFileNameWithoutExtension(path);
            var metas = new List<SpriteMetaData>();
            for (int r = 0; r < rows; r++)
                for (int c = 0; c < cols; c++)
                {
                    var rect = new Rect(c * cell, (rows - 1 - r) * cell, cell, cell);
                    if (IsEmpty(tex, rect)) continue; // ungenutzte Rasterfelder auslassen
                    metas.Add(new SpriteMetaData
                    {
                        name = $"{baseName}_{r}_{c}",
                        rect = rect,
                        alignment = (int)SpriteAlignment.Custom,
                        pivot = new Vector2(0.5f, pivotY),
                    });
                }
#pragma warning disable CS0618
            ti.spritesheet = metas.ToArray();
#pragma warning restore CS0618
            ti.SaveAndReimport();
            Object.DestroyImmediate(tex);

            var result = new Sprite[rows, cols];
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(path))
            {
                if (!(o is Sprite s) || !s.name.StartsWith(baseName + "_")) continue;
                var parts = s.name.Substring(baseName.Length + 1).Split('_');
                if (parts.Length != 2) continue;
                result[int.Parse(parts[0]), int.Parse(parts[1])] = s;
            }
            return result;
        }

        static bool IsEmpty(Texture2D tex, Rect r)
        {
            var px = tex.GetPixels((int)r.x, (int)r.y, (int)r.width, (int)r.height);
            foreach (var p in px) if (p.a > 0.01f) return false;
            return true;
        }

        internal static AnimatorController Controller(string name, Clip[] clips)
        {
            EnsureFolder("Assets/_Project/Art/Animations", name);
            string dir = AnimDir + name + "/";
            string ctrlPath = dir + name + ".controller";
            AssetDatabase.DeleteAsset(ctrlPath);
            var ctrl = AnimatorController.CreateAnimatorControllerAtPath(ctrlPath);
            var sm = ctrl.layers[0].stateMachine;

            foreach (var spec in clips)
            {
                var frames = Slice(CharDir + spec.sheet, spec.cell, out int cols);
                for (int r = 0; r < RowDirs.Length; r++)
                {
                    var list = new List<Sprite>();
                    for (int c = 0; c < cols; c++) if (frames[r, c] != null) list.Add(frames[r, c]);
                    if (list.Count == 0) continue;

                    string stateName = spec.state + "_" + RowDirs[r];
                    var clip = new AnimationClip { frameRate = spec.fps, name = stateName };
                    var keys = new List<ObjectReferenceKeyframe>();
                    for (int i = 0; i < list.Count; i++)
                        keys.Add(new ObjectReferenceKeyframe { time = i / spec.fps, value = list[i] });
                    // Schluesselbild am Ende, damit das letzte Bild seine volle Dauer behaelt
                    keys.Add(new ObjectReferenceKeyframe { time = list.Count / spec.fps, value = list[list.Count - 1] });
                    var binding = EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite");
                    AnimationUtility.SetObjectReferenceCurve(clip, binding, keys.ToArray());
                    var settings = AnimationUtility.GetAnimationClipSettings(clip);
                    settings.loopTime = spec.loop;
                    AnimationUtility.SetAnimationClipSettings(clip, settings);
                    AssetDatabase.CreateAsset(clip, dir + stateName + ".anim");

                    var state = sm.AddState(stateName);
                    state.motion = clip;
                    // idle_S ist als erster angelegt und damit Standardzustand
                }
            }
            EditorUtility.SetDirty(ctrl);
            AssetDatabase.SaveAssets();
            // Neu laden: nach Loeschen und Neuanlegen am selben Pfad haelt Unity sonst kurz die alte Referenz
            AssetDatabase.ImportAsset(ctrlPath, ImportAssetOptions.ForceUpdate);
            return AssetDatabase.LoadAssetAtPath<AnimatorController>(ctrlPath);
        }

        // ------------------------------------------------------------------ Profile und Dialoge
        static Sprite Portrait(string rel)
        {
            string path = CharDir + rel;
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Single;
            ti.spritePixelsPerUnit = 100; // UI: 1 Pixel = 1 Canvas-Einheit
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            ti.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Sprite>(path);
        }

        static NpcProfile Profile(string id, string displayName, string color, string idle, string[] talk)
        {
            string path = $"{DataDir}/NPCs/NpcProfile_{id}.asset";
            var p = AssetDatabase.LoadAssetAtPath<NpcProfile>(path);
            if (p == null)
            {
                p = ScriptableObject.CreateInstance<NpcProfile>();
                AssetDatabase.CreateAsset(p, path);
            }
            p.id = id;
            p.displayName = displayName;
            ColorUtility.TryParseHtmlString(color, out p.nameColor);
            p.portraitIdle = Portrait(idle);
            var talkSprites = new List<Sprite>();
            foreach (var t in talk) talkSprites.Add(Portrait(t));
            p.portraitTalk = talkSprites.ToArray();
            EditorUtility.SetDirty(p);
            return p;
        }

        static DialogueNode N(string id, Speaker s, string text, string next = null, int rel = 0, string flag = null, params DialogueChoice[] choices) =>
            new DialogueNode { id = id, speaker = s, text = text, next = next, relationship = rel, setFlag = flag, choices = new List<DialogueChoice>(choices) };

        static DialogueChoice C(string text, string next, int rel = 0, string flag = null) =>
            new DialogueChoice { text = text, next = next, relationship = rel, setFlag = flag };

        static DialogueAsset Dialog(string folder, string file, params DialogueNode[] nodes)
        {
            EnsureFolder(DataDir + "/Dialoge", folder);
            string path = $"{DataDir}/Dialoge/{folder}/{file}.asset";
            var d = AssetDatabase.LoadAssetAtPath<DialogueAsset>(path);
            if (d != null) return d; // eigene Aenderungen nie ueberschreiben
            d = ScriptableObject.CreateInstance<DialogueAsset>();
            d.startNode = nodes[0].id;
            d.nodes = new List<DialogueNode>(nodes);
            AssetDatabase.CreateAsset(d, path);
            return d;
        }

        static List<DialogueEntry> IlhanDialogs()
        {
            var kennen = Dialog("Ilhan_Bartender", "Dialog_IlhanBar_Kennenlernen",
                N("start", Speaker.Npc, "Setz dich, wo Platz ist. Ein Bier, ein Tee oder einfach Gesellschaft? Alles kostet hier dasselbe: ein paar ehrliche Worte.", null, 0, "ilhan_bar_kennengelernt",
                    C("Ein Tee, bitte.", "tee", 1),
                    C("Was ist hier los im Dorf?", "dorf"),
                    C("Ich will nur nicht draußen sein.", "draussen")),
                N("tee", Speaker.Npc, "Kamille mit Honig. Hilft gegen Albträume. Zumindest redet man es sich ein."),
                N("dorf", Speaker.Npc, "Nachts klopft es. Wer aufmacht, kommt nicht wieder. Wer zu laut zuhört, schläft schlecht.", "dorf2"),
                N("dorf2", Speaker.Npc, "Merk dir: Echte Nachbarn betteln um Einlass. Die anderen sagen immer denselben Satz."),
                N("draussen", Speaker.Npc, "Kluger Mann. Oder kluge Frau. Bleib, solange die Laternen brennen."));
            var alltag = Dialog("Ilhan_Bartender", "Dialog_IlhanBar_Alltag",
                N("start", Speaker.Npc, "Noch einen Schluck? Die Nacht ist lang.", null, 0, null,
                    C("Gibt es Neuigkeiten?", "neu"),
                    C("Danke, nein.", "nein")),
                N("neu", Speaker.Npc, "Der Sheriff läutet bald die Glocke. Dann will keiner mehr auf der Straße sein."),
                N("nein", Speaker.Npc, "Dann pass auf dich auf. Und verriegel die Tür richtig."));
            return new List<DialogueEntry>
            {
                new DialogueEntry { dialogue = kennen, onlyOnce = true },
                new DialogueEntry { dialogue = alltag },
            };
        }

        static List<DialogueEntry> BulutDialogs()
        {
            var kennen = Dialog("Bulut_Sheriff", "Dialog_Bulut_Kennenlernen",
                N("start", Speaker.Npc, "Halt. Ich kenne hier jedes Gesicht. Deins nicht. Name, Herkunft, Absicht.", null, 0, "bulut_kennengelernt",
                    C("Ich bin nur auf der Durchreise.", "reise"),
                    C("Ich will helfen, die Nacht zu überstehen.", "helfen", 1),
                    C("Seit wann fragt hier einer?", "frech", -2)),
                N("reise", Speaker.Npc, "Durchreise endet bei Dämmerung. Danach sitzt du fest. Wie wir alle."),
                N("helfen", Speaker.Npc, "Hilfe kann ich brauchen. Aber wer hilft, hört auf mich. Wenn ich die Glocke läute, bist du drinnen."),
                N("frech", Speaker.Npc, "Seit der Wald nachts Besuch schickt. Merk dir das."));
            var alltag = Dialog("Bulut_Sheriff", "Dialog_Bulut_Alltag",
                N("start", Speaker.Npc, "Ruhig heute. Zu ruhig.", null, 0, null,
                    C("Wann läutest du die Glocke?", "glocke"),
                    C("Alles in Ordnung?", "ok")),
                N("glocke", Speaker.Npc, "Wenn die Dämmerung einbricht. Dann Türen zu, Balken vor, Licht an."),
                N("ok", Speaker.Npc, "Solange keiner grinst, der es nicht sollte."));
            return new List<DialogueEntry>
            {
                new DialogueEntry { dialogue = kennen, onlyOnce = true },
                new DialogueEntry { dialogue = alltag },
            };
        }

        static List<DialogueEntry> GastDialogs()
        {
            var erst = Dialog("Gast", "Dialog_Gast_Erstkontakt",
                N("start", Speaker.Npc, "Guten Tag. Ich bin zu Besuch. Ich bin immer zu Besuch.", null, 0, "gast_kennengelernt",
                    C("Wie heißt du?", "name"),
                    C("Woher kommst du?", "woher"),
                    C("Ich habe zu tun.", "tschuess")),
                N("name", Speaker.Npc, "Ich habe den Namen eines Mannes, der verschwunden ist. Er passt mir gut. Möchtest du ihn hören?"),
                N("woher", Speaker.Npc, "Von weit her. Ich warte gern. Eine Nacht mehr oder weniger macht mir nichts."),
                N("tschuess", Speaker.Npc, "Natürlich. Ich komme wieder. Ich klopfe dreimal."));
            var alltag = Dialog("Gast", "Dialog_Gast_Alltag",
                N("start", Speaker.Npc, "Eins. Zwei. Drei. ... Entschuldige, ich zähle gern.", null, 0, null,
                    C("Was zählst du?", "zaehlen"),
                    C("Geh weg.", "weg", -1)),
                N("zaehlen", Speaker.Npc, "Gäste. Jeder zählt. Du zählst auch, du weißt es nur noch nicht."),
                N("weg", Speaker.Npc, "Ich gehe. Ich komme wieder."));
            return new List<DialogueEntry>
            {
                new DialogueEntry { dialogue = erst, onlyOnce = true },
                new DialogueEntry { dialogue = alltag },
            };
        }

        static List<DialogueEntry> HausfrauDialogs()
        {
            var erst = Dialog("Hausfrau", "Dialog_Hausfrau_Erstkontakt",
                N("start", Speaker.Npc, "Ach, du bist so dünn geworden, Liebes. Ich habe Brot. Und Suppe, wenn du magst.", null, 0, "hausfrau_kennengelernt",
                    C("Danke, gern.", "annehmen", 1),
                    C("Nein danke.", "ablehnen", -1),
                    C("Wer sind Sie?", "wer")),
                N("annehmen", Speaker.Npc, "Das ist brav. Du musst essen, solange es noch geht."),
                N("ablehnen", Speaker.Npc, "Wie du meinst. Die Suppe wird kalt. Ich merke mir, wer sie verschmäht."),
                N("wer", Speaker.Npc, "Eine Nachbarin. Die Einzige, die noch an dich denkt. Hörst du, wie still es ist?"));
            var alltag = Dialog("Hausfrau", "Dialog_Hausfrau_Alltag",
                N("start", Speaker.Npc, "Mmm-mm-mmm ... Ach, du. Das Tablett wird schwer.", null, 0, null,
                    C("Was summst du da?", "lied"),
                    C("Ich muss weiter.", "weiter")),
                N("lied", Speaker.Npc, "Ein altes Lied. Kennst du es nicht? Dann kennst du das Dorf nicht gut genug."),
                N("weiter", Speaker.Npc, "Geh nur. Ich bringe dir morgen etwas. Mach auf, wenn ich klopfe."));
            return new List<DialogueEntry>
            {
                new DialogueEntry { dialogue = erst, onlyOnce = true },
                new DialogueEntry { dialogue = alltag },
            };
        }

        // ------------------------------------------------------------------ Prefabs und Szene
        static GameObject MakePrefab(string name, AnimatorController ctrl, AnimatorController revealed, NpcProfile profile,
            List<DialogueEntry> entries, float wanderRadius, bool monster)
        {
            string path = PrefabDir + name + ".prefab";
            var contents = PrefabUtility.LoadPrefabContents(BasePrefab); // gleiche Bauweise wie der bestehende Ilhan
            contents.name = name;

            var visual = contents.transform.Find("Visual");
            var anim = visual.GetComponent<Animator>();
            anim.runtimeAnimatorController = ctrl;
            var sr = visual.GetComponent<SpriteRenderer>();
            sr.sprite = FirstSprite(ctrl);

            var wander = new SerializedObject(contents.GetComponent<WanderBehavior>());
            wander.FindProperty("radius").floatValue = wanderRadius;
            wander.ApplyModifiedPropertiesWithoutUndo();

            DialogueSetup.MakeTalkable(contents, profile, entries);

            if (monster)
            {
                var m = contents.AddComponent<MonsterNpc>();
                var so = new SerializedObject(m);
                so.FindProperty("animator").objectReferenceValue = anim;
                so.FindProperty("disguisedController").objectReferenceValue = ctrl;
                so.FindProperty("revealedController").objectReferenceValue = revealed;
                so.ApplyModifiedPropertiesWithoutUndo();
            }

            PrefabUtility.SaveAsPrefabAsset(contents, path);
            PrefabUtility.UnloadPrefabContents(contents);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceUpdate);
            return AssetDatabase.LoadAssetAtPath<GameObject>(path);
        }

        static Sprite FirstSprite(AnimatorController ctrl)
        {
            foreach (var st in ctrl.layers[0].stateMachine.states)
            {
                if (st.state.name != "idle_S") continue;
                var clip = (AnimationClip)st.state.motion;
                var keys = AnimationUtility.GetObjectReferenceCurve(clip, EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite"));
                return keys.Length > 0 ? (Sprite)keys[0].value : null;
            }
            return null;
        }

        static void Place(GameObject prefab, Vector3 pos)
        {
            var old = GameObject.Find(prefab.name);
            if (old != null) Object.DestroyImmediate(old); // erneutes Ausfuehren ersetzt die Testinstanz
            var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            go.transform.position = pos;
            Undo.RegisterCreatedObjectUndo(go, "NPC platzieren");
        }
    }
}
