using System.Collections;
using UnityEngine;

namespace Nightward.Opening
{
    /// <summary>
    /// Ton der Opening Sequence, bewusst leise und im Hintergrund: duestere Intro-Melodie, Autoradio (gemuetlicher Walzer),
    /// Rauschen, Voegel, Motor, Glocke, Raben, Rascheln beim Untersuchen, Schreibmaschinen-Tick und NPC-Mumble.
    /// Solange keine echten Clips im Inspector stecken, werden weiche Platzhalter per Code erzeugt.
    /// Echte Clips einfach in die Slots ziehen, die Platzhalter entfallen dann.
    /// </summary>
    public class OpeningAudio : MonoBehaviour
    {
        const int Rate = 22050;

        [Header("Clips (leer = Platzhalter)")]
        [SerializeField] AudioClip introMusic;
        [SerializeField] AudioClip radioSong;
        [SerializeField] AudioClip radioStatic;
        [SerializeField] AudioClip birds;
        [SerializeField] AudioClip engine;
        [SerializeField] AudioClip bell;
        [SerializeField] AudioClip raven;
        [SerializeField] AudioClip rustle;
        [SerializeField] AudioClip typeTick;
        [SerializeField] AudioClip[] mumble = new AudioClip[0];

        [Header("Lautstaerke (alles im Hintergrund)")]
        [SerializeField, Range(0f, 1f)] float introVolume = 0.22f;
        [SerializeField, Range(0f, 1f)] float radioVolume = 0.12f;
        [SerializeField, Range(0f, 1f)] float staticVolume = 0.045f;
        [SerializeField, Range(0f, 1f)] float birdsVolume = 0.1f;
        [SerializeField, Range(0f, 1f)] float engineVolume = 0.07f;
        [SerializeField, Range(0f, 1f)] float bellVolume = 0.35f;
        [SerializeField, Range(0f, 1f)] float ravenVolume = 0.12f;
        [SerializeField, Range(0f, 1f)] float rustleVolume = 0.12f;
        [SerializeField, Range(0f, 1f)] float typeVolume = 0.035f;
        [SerializeField, Range(0f, 1f)] float mumbleVolume = 0.12f;

        AudioSource musicSrc, radioSrc, staticSrc, birdsSrc, engineSrc, sfxSrc, mumbleSrc, rustleSrc;
        float mumbleTimer;
        float mumblePitch = 1f;
        bool engineOn;

        /// <summary>Solange true, murmelt der Mumble-Ton in kurzen, weichen Silben.</summary>
        public bool Mumbling { get; set; }

        void Awake()
        {
            if (introMusic == null) introMusic = MakeIntroMusic();
            if (radioSong == null) radioSong = MakeRadioWaltz();
            if (radioStatic == null) radioStatic = MakeHiss();
            if (birds == null) birds = MakeBirds();
            if (engine == null) engine = MakeEngine();
            if (bell == null) bell = MakeBell();
            if (raven == null) raven = MakeRaven();
            if (rustle == null) rustle = MakeRustle();
            if (typeTick == null) typeTick = MakeTick();
            if (mumble.Length == 0) mumble = new[] { MakeBlip(0), MakeBlip(1), MakeBlip(2), MakeBlip(3) };

            musicSrc = Source(introMusic, true);
            radioSrc = Source(radioSong, true);
            staticSrc = Source(radioStatic, true);
            birdsSrc = Source(birds, true);
            engineSrc = Source(engine, true);
            rustleSrc = Source(rustle, true);
            sfxSrc = Source(null, false);
            mumbleSrc = Source(null, false);
        }

        AudioSource Source(AudioClip clip, bool loop)
        {
            var s = gameObject.AddComponent<AudioSource>();
            s.clip = clip;
            s.loop = loop;
            s.playOnAwake = false;
            s.volume = 0f;
            s.spatialBlend = 0f;
            return s;
        }

        void Update()
        {
            // Motor nur, solange jemand am Steuer sitzt und die Fahrt begonnen hat
            if (!engineOn) engineSrc.volume = Mathf.MoveTowards(engineSrc.volume, 0f, Time.unscaledDeltaTime * 0.2f);

            if (!Mumbling || mumble.Length == 0) return;
            mumbleTimer -= Time.unscaledDeltaTime;
            if (mumbleTimer > 0f) return;
            mumbleTimer = Random.Range(0.11f, 0.17f);
            mumbleSrc.pitch = mumblePitch * Random.Range(0.92f, 1.08f);
            mumbleSrc.PlayOneShot(mumble[Random.Range(0, mumble.Length)], mumbleVolume);
        }

        /// <summary>Tonhoehe der Stimme, z. B. 0.8 fuer Bulut.</summary>
        public void SetVoice(float pitch) => mumblePitch = pitch;

        // ------------------------------------------------------------ Intro

        public void IntroMusic(bool on, float time = 2f)
        {
            if (on) Play(musicSrc, 0f);
            StartCoroutine(FadeTo(musicSrc, on ? introVolume : 0f, time));
        }

        // ------------------------------------------------------------ Fahrt

        public void StartDriveAmbience(float time = 2.5f)
        {
            Play(radioSrc, 0f);
            Play(birdsSrc, 0f);
            Play(engineSrc, 0f);
            StartCoroutine(FadeTo(radioSrc, radioVolume, time));
            StartCoroutine(FadeTo(birdsSrc, birdsVolume, time));
        }

        /// <summary>Step 4: Das Lied geht in leises Rauschen ueber, die Voegel verstummen.</summary>
        public void RadioDies(float time = 3f)
        {
            Play(staticSrc, 0f);
            StartCoroutine(FadeTo(radioSrc, 0f, time));
            StartCoroutine(FadeTo(staticSrc, staticVolume, time));
            StartCoroutine(FadeTo(birdsSrc, 0f, time * 0.8f));
        }

        public void SetStatic(float factor, float time = 0.8f) => StartCoroutine(FadeTo(staticSrc, staticVolume * factor, time));

        /// <summary>Jeden Frame vom Auto: an/aus und Tempo 0..1.</summary>
        public void Engine(bool on, float speed01 = 0f)
        {
            engineOn = on;
            if (!on) return;
            if (!engineSrc.isPlaying) engineSrc.Play();
            float target = engineVolume * Mathf.Lerp(0.6f, 1f, speed01);
            engineSrc.volume = Mathf.MoveTowards(engineSrc.volume, target, Time.deltaTime * 0.15f);
            engineSrc.pitch = Mathf.Lerp(engineSrc.pitch, Mathf.Lerp(0.85f, 1.2f, speed01), Time.deltaTime * 2f);
        }

        // ------------------------------------------------------------ Einzelne Klaenge

        public Coroutine Bell(int strikes, float gap = 2.2f) => StartCoroutine(BellRoutine(strikes, gap));

        IEnumerator BellRoutine(int strikes, float gap)
        {
            for (int i = 0; i < strikes; i++)
            {
                sfxSrc.PlayOneShot(bell, bellVolume);
                yield return new WaitForSeconds(gap);
            }
        }

        public void Raven(float pitch = 1f)
        {
            sfxSrc.pitch = pitch;
            sfxSrc.PlayOneShot(raven, ravenVolume);
            sfxSrc.pitch = 1f;
        }

        /// <summary>Rascheln/Tasten beim Untersuchen.</summary>
        public void Rustle(bool on) => StartCoroutine(FadeTo(rustleSrc, on ? rustleVolume : 0f, 0.4f, playIfNeeded: on));

        /// <summary>Leiser Anschlag fuer Schreibmaschinen-Text.</summary>
        public void Tick() => sfxSrc.PlayOneShot(typeTick, typeVolume * Random.Range(0.8f, 1.2f));

        public void StopAll(float time = 1.5f)
        {
            foreach (var s in new[] { musicSrc, radioSrc, staticSrc, birdsSrc, rustleSrc }) StartCoroutine(FadeTo(s, 0f, time));
            engineOn = false;
        }

        static void Play(AudioSource s, float volume)
        {
            s.volume = volume;
            if (!s.isPlaying) s.Play();
        }

        static IEnumerator FadeTo(AudioSource s, float target, float time, bool playIfNeeded = true)
        {
            if (playIfNeeded && target > 0f && !s.isPlaying) s.Play();
            float start = s.volume;
            for (float t = 0f; t < time; t += Time.unscaledDeltaTime)
            {
                s.volume = Mathf.Lerp(start, target, t / time);
                yield return null;
            }
            s.volume = target;
        }

        // ------------------------------------------------------------ Platzhalter-Klaenge (weich: Sinus/Dreieck, keine Rechtecke)

        static AudioClip Clip(string name, float[] data)
        {
            var c = AudioClip.Create(name, data.Length, 1, Rate, false);
            c.SetData(data, 0);
            return c;
        }

        static float Note(float semitonesFromA4) => 440f * Mathf.Pow(2f, semitonesFromA4 / 12f);
        static float Tri(float phase) { float p = phase - Mathf.Floor(phase); return 4f * Mathf.Abs(p - 0.5f) - 1f; }

        /// <summary>Weicher "Klavier"-Ton: Grundton + leise Obertoene, schneller Anschlag, langes Ausklingen.</summary>
        static float Pluck(float f, float t, float decay)
        {
            if (t < 0f) return 0f;
            float env = Mathf.Min(1f, t * 120f) * Mathf.Exp(-t * decay);
            float w = 2f * Mathf.PI * f * t;
            return (Mathf.Sin(w) + 0.35f * Mathf.Sin(2f * w) + 0.12f * Mathf.Sin(3f * w)) * env;
        }

        static void Normalize(float[] d, float peak)
        {
            float max = 0.0001f;
            foreach (var v in d) max = Mathf.Max(max, Mathf.Abs(v));
            for (int i = 0; i < d.Length; i++) d[i] = d[i] / max * peak;
        }

        /// <summary>Langsam und duester: Moll-Flaeche (verstimmte Sinus-Paare) und vereinzelte, weit ausklingende Toene.</summary>
        static AudioClip MakeIntroMusic()
        {
            const float seconds = 32f;
            int len = Mathf.RoundToInt(seconds * Rate);
            var d = new float[len];
            // Akkorde a-Moll, F, C, E (je 8 s), als tiefe Flaeche
            float[][] chords = { new[] { -24f, -17f, -12f }, new[] { -28f, -21f, -16f }, new[] { -33f, -26f, -21f }, new[] { -29f, -22f, -17f } };
            // Melodie (Halbtoene relativ zu A4) mit Einsatzzeiten
            (float t, float n)[] melody =
            {
                (0.5f, -9f), (3f, -5f), (5.5f, -7f), (8.5f, -9f), (11f, -12f), (14f, -10f),
                (16.5f, -9f), (19f, -5f), (21.5f, -4f), (24.5f, -5f), (27f, -9f), (29.5f, -8f),
            };
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)Rate;
                int ci = Mathf.Min(3, (int)(t / 8f));
                float local = t - ci * 8f;
                float env = Mathf.SmoothStep(0f, 1f, Mathf.Min(1f, local / 2.5f)) * Mathf.SmoothStep(0f, 1f, Mathf.Min(1f, (8f - local) / 2.5f));
                float s = 0f;
                foreach (var n in chords[ci])
                {
                    float f = Note(n);
                    s += (Mathf.Sin(2f * Mathf.PI * f * t) + Mathf.Sin(2f * Mathf.PI * f * 1.004f * t)) * 0.12f * env;
                }
                foreach (var m in melody) s += Pluck(Note(m.n), t - m.t, 0.9f) * 0.28f;
                d[i] = s;
            }
            // Nahtlose Schleife: Ende in den Anfang blenden
            int fade = Rate * 2;
            for (int i = 0; i < fade; i++) { float k = i / (float)fade; d[i] = d[i] * k + d[len - fade + i] * (1f - k); }
            Normalize(d, 0.6f);
            return Clip("Intro_Platzhalter", d);
        }

        /// <summary>Gemuetlicher, langsamer Walzer wie aus einem alten Autoradio: tiefer Bass auf 1, weiche Akkorde auf 2 und 3, ruhige Melodie.</summary>
        static AudioClip MakeRadioWaltz()
        {
            const float bpm = 96f;
            float beat = 60f / bpm;
            // Takte: F C C F | Bb F C F (Grundton relativ zu A4)
            float[] roots = { -16f, -9f, -9f, -16f, -11f, -16f, -9f, -16f };
            bool[] major = { true, true, true, true, true, true, true, true };
            // Melodie pro Takt: 3 Viertel in F-Dur (0 = F, 4 = A, 7 = C), -99 = halten
            float[] melody =
            {
                0f, 4f, 7f,     7f, 5f, 4f,     2f, 4f, 5f,     4f, -99f, -99f,
                5f, 7f, 9f,     7f, 5f, 4f,     2f, 0f, 2f,     0f, -99f, -99f,
            };
            int bars = roots.Length;
            int len = Mathf.RoundToInt(bars * 3 * beat * Rate);
            var d = new float[len];
            var rng = new System.Random(7);
            float lp = 0f, lastNoteStart = 0f, lastNote = melody[0];
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)Rate;
                int b = Mathf.Min(bars * 3 - 1, (int)(t / beat));
                float inBeat = t - b * beat;
                int bar = b / 3, pos = b % 3;
                float root = roots[bar];
                float third = major[bar] ? 4f : 3f;
                float s = 0f;
                if (pos == 0) s += Pluck(Note(root - 12f), inBeat, 3f) * 0.5f;
                else
                {
                    s += Pluck(Note(root), inBeat, 4f) * 0.12f;
                    s += Pluck(Note(root + third), inBeat, 4f) * 0.12f;
                    s += Pluck(Note(root + 7f), inBeat, 4f) * 0.1f;
                }
                float m = melody[b % melody.Length];
                if (m > -99f && inBeat < 1f / Rate * 2f) { lastNote = m; lastNoteStart = b * beat; }
                float mt = t - lastNoteStart;
                float vib = 1f + 0.004f * Mathf.Sin(2f * Mathf.PI * 4.5f * t);
                float f = Note(lastNote - 4f) * vib;   // F-Dur, Grundton F4
                float menv = Mathf.Min(1f, mt * 25f) * Mathf.Exp(-mt * 0.9f);
                s += (Tri(f * t) * 0.18f + Mathf.Sin(2f * Mathf.PI * f * t) * 0.2f) * menv;
                // Radio: weicher Tiefpass, kaum Knistern
                lp += (s - lp) * 0.22f;
                d[i] = lp + ((float)rng.NextDouble() * 2f - 1f) * 0.004f;
            }
            Normalize(d, 0.55f);
            return Clip("Radio_Walzer_Platzhalter", d);
        }

        /// <summary>Leises, weiches Rauschen (stark gefiltert, kein Knacken).</summary>
        static AudioClip MakeHiss()
        {
            var rng = new System.Random(3);
            int len = Rate * 4;
            var d = new float[len];
            float a = 0f, b = 0f;
            for (int i = 0; i < len; i++)
            {
                float n = (float)rng.NextDouble() * 2f - 1f;
                a += (n - a) * 0.08f;
                b += (a - b) * 0.08f;
                d[i] = b;
            }
            int fade = Rate / 2;
            for (int i = 0; i < fade; i++) { float k = i / (float)fade; d[i] = d[i] * k + d[len - fade + i] * (1f - k); }
            Normalize(d, 0.5f);
            return Clip("Rauschen_Platzhalter", d);
        }

        /// <summary>Vereinzelte, ruhige Vogelrufe: wenige Toene mit langen Pausen.</summary>
        static AudioClip MakeBirds()
        {
            var rng = new System.Random(11);
            const float seconds = 16f;
            int len = Mathf.RoundToInt(seconds * Rate);
            var d = new float[len];
            float time = 0.8f;
            while (time < seconds - 1.5f)
            {
                int notes = 2 + rng.Next(3);
                float baseF = 1700f + (float)rng.NextDouble() * 900f;
                for (int c = 0; c < notes; c++)
                {
                    float cs = time + c * (0.22f + (float)rng.NextDouble() * 0.12f);
                    float dur = 0.12f + (float)rng.NextDouble() * 0.1f;
                    float step = c % 2 == 0 ? 1f : 1.12f;
                    int i0 = Mathf.RoundToInt(cs * Rate), n = Mathf.RoundToInt(dur * Rate);
                    float phase = 0f;
                    for (int i = 0; i < n && i0 + i < len; i++)
                    {
                        float u = i / (float)n;
                        float f = baseF * step * (1f + 0.06f * Mathf.Sin(u * Mathf.PI));
                        phase += f / Rate;
                        float env = Mathf.Sin(u * Mathf.PI);
                        d[i0 + i] += Mathf.Sin(2f * Mathf.PI * phase) * env * env * 0.25f;
                    }
                }
                time += 2.2f + (float)rng.NextDouble() * 2.5f;
            }
            Normalize(d, 0.45f);
            return Clip("Voegel_Platzhalter", d);
        }

        /// <summary>Leises, tiefes Brummen eines alten Motors (weich, leicht schwankend).</summary>
        static AudioClip MakeEngine()
        {
            var rng = new System.Random(5);
            int len = Rate * 2;
            var d = new float[len];
            float lp = 0f;
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)Rate;
                float wob = 1f + 0.03f * Mathf.Sin(2f * Mathf.PI * 2f * t);   // 2 Hz, passt in 2 s
                float s = Mathf.Sin(2f * Mathf.PI * 40f * wob * t) * 0.5f + Mathf.Sin(2f * Mathf.PI * 80f * t) * 0.2f
                          + Mathf.Sin(2f * Mathf.PI * 20f * t) * 0.25f;
                float n = (float)rng.NextDouble() * 2f - 1f;
                lp += (n - lp) * 0.02f;
                d[i] = s + lp * 0.4f;
            }
            Normalize(d, 0.5f);
            return Clip("Motor_Platzhalter", d);
        }

        static AudioClip MakeBell()
        {
            const float seconds = 5f, f0 = 174f;
            float[] partials = { 0.5f, 1f, 1.19f, 1.5f, 2f, 2.74f, 3.0f };
            float[] amps = { 0.35f, 0.5f, 0.28f, 0.2f, 0.16f, 0.08f, 0.06f };
            float[] decay = { 0.5f, 0.8f, 1.2f, 1.5f, 2f, 3f, 3.5f };
            int len = Mathf.RoundToInt(seconds * Rate);
            var d = new float[len];
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)Rate;
                float s = 0f;
                for (int p = 0; p < partials.Length; p++)
                    s += Mathf.Sin(2f * Mathf.PI * f0 * partials[p] * t) * amps[p] * Mathf.Exp(-t * decay[p]);
                d[i] = s * Mathf.Min(1f, t * 200f);
            }
            Normalize(d, 0.7f);
            return Clip("Glocke_Platzhalter", d);
        }

        /// <summary>Rabe: rauer, abfallender Ruf "kraa".</summary>
        static AudioClip MakeRaven()
        {
            var rng = new System.Random(9);
            const float seconds = 0.45f;
            int len = Mathf.RoundToInt(seconds * Rate);
            var d = new float[len];
            float phase = 0f, lp = 0f;
            for (int i = 0; i < len; i++)
            {
                float u = i / (float)len;
                float f = Mathf.Lerp(420f, 300f, u);
                phase += f / Rate;
                float saw = (phase - Mathf.Floor(phase)) * 2f - 1f;
                float n = (float)rng.NextDouble() * 2f - 1f;
                float s = saw * 0.6f + n * 0.35f;
                lp += (s - lp) * 0.3f;
                float env = Mathf.Min(1f, u * 20f) * Mathf.Pow(1f - u, 1.5f);
                d[i] = lp * env;
            }
            Normalize(d, 0.5f);
            return Clip("Rabe_Platzhalter", d);
        }

        /// <summary>Rascheln und leises Klopfen beim Untersuchen (Schleife).</summary>
        static AudioClip MakeRustle()
        {
            var rng = new System.Random(21);
            int len = Rate * 3;
            var d = new float[len];
            float lp = 0f;
            for (int k = 0; k < 9; k++)
            {
                int start = rng.Next(0, len - Rate / 3);
                int n = Rate / 6 + rng.Next(Rate / 8);
                for (int i = 0; i < n; i++)
                {
                    float u = i / (float)n;
                    float noise = (float)rng.NextDouble() * 2f - 1f;
                    lp += (noise - lp) * 0.35f;
                    d[start + i] += lp * Mathf.Sin(u * Mathf.PI) * 0.4f;
                }
            }
            for (int k = 0; k < 4; k++)
            {
                int start = rng.Next(0, len - Rate / 10);
                for (int i = 0; i < Rate / 12; i++)
                {
                    float t = i / (float)Rate;
                    d[start + i] += Mathf.Sin(2f * Mathf.PI * 180f * t) * Mathf.Exp(-t * 60f) * 0.5f;
                }
            }
            Normalize(d, 0.5f);
            return Clip("Rascheln_Platzhalter", d);
        }

        static AudioClip MakeTick()
        {
            var rng = new System.Random(4);
            int len = Rate / 25;
            var d = new float[len];
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)Rate;
                float n = (float)rng.NextDouble() * 2f - 1f;
                d[i] = (n * 0.5f + Mathf.Sin(2f * Mathf.PI * 1200f * t) * 0.5f) * Mathf.Exp(-t * 300f);
            }
            Normalize(d, 0.6f);
            return Clip("Tick_Platzhalter", d);
        }

        /// <summary>Weiche, gedaempfte Silbe ("mm", "hm") in vier Varianten.</summary>
        static AudioClip MakeBlip(int variant)
        {
            float[] freqs = { 140f, 155f, 128f, 165f };
            float[] formant = { 420f, 520f, 360f, 480f };
            const float seconds = 0.1f;
            int len = Mathf.RoundToInt(seconds * Rate);
            var d = new float[len];
            for (int i = 0; i < len; i++)
            {
                float t = i / (float)Rate;
                float u = i / (float)len;
                float env = Mathf.Sin(u * Mathf.PI);
                float s = Mathf.Sin(2f * Mathf.PI * freqs[variant] * t) * 0.6f + Mathf.Sin(2f * Mathf.PI * formant[variant] * t) * 0.15f;
                d[i] = s * env * env;
            }
            Normalize(d, 0.5f);
            return Clip("Mumble_" + variant, d);
        }
    }
}
