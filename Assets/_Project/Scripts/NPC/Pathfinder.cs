using System.Collections.Generic;
using UnityEngine;

namespace Nightward.NPC
{
    /// <summary>
    /// A* auf dem NavGrid, 8 Richtungen. Diagonal nur, wenn beide angrenzenden geraden Zellen frei sind,
    /// damit niemand ueber Ecken von Hindernissen schneidet. Zellen direkt an Hindernissen kosten etwas mehr,
    /// so laufen NPCs nicht unnoetig an Waenden und Baumstaemmen entlang.
    /// Danach wird der Pfad per Sichtlinie geglaettet: aus dem Zickzack der Zellen werden wenige gerade Strecken.
    /// Arbeitsspeicher wird zwischen Aufrufen wiederverwendet, deshalb nicht threadsicher.
    /// </summary>
    public class Pathfinder
    {
        const int StraightCost = 10, DiagonalCost = 14; // 14 ~ 10 * Wurzel 2
        const int NearWallCost = 6; // Aufschlag fuer Zellen direkt an Hindernissen: Wege laufen lieber mittig

        static readonly int[] DX = { 1, -1, 0, 0, 1, 1, -1, -1 };
        static readonly int[] DY = { 0, 0, 1, -1, 1, -1, 1, -1 };

        readonly NavGrid grid;
        readonly int[] gCost;
        readonly int[] parent;
        readonly int[] visitedStamp; // statt Arrays zu leeren: Zelle gilt nur, wenn Stamp == aktueller Lauf
        readonly int[] closedStamp;
        readonly MinHeap open;
        int run;

        public Pathfinder(NavGrid grid)
        {
            this.grid = grid;
            int n = grid.Width * grid.Height;
            gCost = new int[n];
            parent = new int[n];
            visitedStamp = new int[n];
            closedStamp = new int[n];
            open = new MinHeap(n);
        }

        /// <summary>Liefert Wegpunkte in Weltkoordinaten (ohne Startpunkt) oder null, wenn unerreichbar.</summary>
        public List<Vector2> FindPath(Vector2 fromWorld, Vector2 toWorld)
        {
            if (!grid.TryGetNearestWalkable(grid.WorldToCell(fromWorld), out var start, 3)) return null;
            if (!grid.TryGetNearestWalkable(grid.WorldToCell(toWorld), out var goal)) return null;
            if (grid.RegionAt(start.x, start.y) != grid.RegionAt(goal.x, goal.y)) return null; // spart den ganzen A*-Lauf

            // Liegt das Ziel selbst in einer blockierten Zelle, endet der Weg am naechsten freien Feld
            bool goalExact = grid.IsWalkable(toWorld);
            Vector2 finalPoint = goalExact ? toWorld : grid.CellToWorld(goal.x, goal.y);

            if (start == goal) return new List<Vector2> { finalPoint };
            if (grid.HasLineOfSight(fromWorld, finalPoint)) return new List<Vector2> { finalPoint };

            List<Vector2Int> cells = Search(start, goal);
            if (cells == null) return null;
            return Smooth(fromWorld, cells, finalPoint);
        }

        List<Vector2Int> Search(Vector2Int start, Vector2Int goal)
        {
            int w = grid.Width;
            if (++run == int.MaxValue)
            {
                System.Array.Clear(visitedStamp, 0, visitedStamp.Length);
                System.Array.Clear(closedStamp, 0, closedStamp.Length);
                run = 1;
            }
            open.Clear();

            int s = start.x + start.y * w, g = goal.x + goal.y * w;
            gCost[s] = 0;
            parent[s] = -1;
            visitedStamp[s] = run;
            open.Push(s, Heuristic(start.x, start.y, goal));

            while (open.Count > 0)
            {
                int cur = open.Pop();
                if (closedStamp[cur] == run) continue; // veralteter Heap-Eintrag
                closedStamp[cur] = run;
                if (cur == g) return Reconstruct(g);

                int cx = cur % w, cy = cur / w;
                for (int i = 0; i < 8; i++)
                {
                    int nx = cx + DX[i], ny = cy + DY[i];
                    if (!grid.IsWalkable(nx, ny)) continue;
                    bool diagonal = i >= 4;
                    if (diagonal && (!grid.IsWalkable(cx + DX[i], cy) || !grid.IsWalkable(cx, cy + DY[i]))) continue;

                    int n = nx + ny * w;
                    if (closedStamp[n] == run) continue;
                    int cost = gCost[cur] + (diagonal ? DiagonalCost : StraightCost) + (grid.IsNearWall(nx, ny) ? NearWallCost : 0);
                    if (visitedStamp[n] == run && cost >= gCost[n]) continue;

                    visitedStamp[n] = run;
                    gCost[n] = cost;
                    parent[n] = cur;
                    open.Push(n, cost + Heuristic(nx, ny, goal)); // Duplikate erlaubt, siehe closedStamp oben
                }
            }
            return null;
        }

        // Oktil-Distanz: exakte Kosten auf freiem 8-Richtungs-Raster
        static int Heuristic(int x, int y, Vector2Int goal)
        {
            int dx = Mathf.Abs(x - goal.x), dy = Mathf.Abs(y - goal.y);
            return StraightCost * (dx + dy) + (DiagonalCost - 2 * StraightCost) * Mathf.Min(dx, dy);
        }

        List<Vector2Int> Reconstruct(int goal)
        {
            int w = grid.Width;
            var cells = new List<Vector2Int>();
            for (int c = goal; c != -1; c = parent[c]) cells.Add(new Vector2Int(c % w, c / w));
            cells.Reverse();
            return cells;
        }

        // Von der aktuellen Position aus den weitesten noch sichtbaren Wegpunkt nehmen, dann von dort weiter.
        List<Vector2> Smooth(Vector2 from, List<Vector2Int> cells, Vector2 finalPoint)
        {
            var result = new List<Vector2>();
            Vector2 anchor = from;
            int i = 1;
            while (i < cells.Count)
            {
                int furthest = i;
                for (int j = cells.Count - 1; j > i; j--)
                {
                    Vector2 p = j == cells.Count - 1 ? finalPoint : grid.CellToWorld(cells[j].x, cells[j].y);
                    if (grid.HasLineOfSight(anchor, p)) { furthest = j; break; }
                }
                anchor = furthest == cells.Count - 1 ? finalPoint : grid.CellToWorld(cells[furthest].x, cells[furthest].y);
                result.Add(anchor);
                i = furthest + 1;
            }
            if (result.Count == 0 || result[result.Count - 1] != finalPoint) result.Add(finalPoint);
            return result;
        }

        /// <summary>Binaerer Min-Heap ueber Zellindizes.</summary>
        class MinHeap
        {
            int[] items, keys;
            public int Count { get; private set; }

            public MinHeap(int capacity)
            {
                items = new int[Mathf.Max(16, capacity)];
                keys = new int[items.Length];
            }

            public void Clear() => Count = 0;

            public void Push(int item, int key)
            {
                if (Count == items.Length)
                {
                    System.Array.Resize(ref items, Count * 2);
                    System.Array.Resize(ref keys, Count * 2);
                }
                int i = Count++;
                while (i > 0)
                {
                    int p = (i - 1) / 2;
                    if (keys[p] <= key) break;
                    items[i] = items[p]; keys[i] = keys[p];
                    i = p;
                }
                items[i] = item; keys[i] = key;
            }

            public int Pop()
            {
                int top = items[0];
                int lastItem = items[--Count], lastKey = keys[Count];
                int i = 0;
                while (true)
                {
                    int c = 2 * i + 1;
                    if (c >= Count) break;
                    if (c + 1 < Count && keys[c + 1] < keys[c]) c++;
                    if (keys[c] >= lastKey) break;
                    items[i] = items[c]; keys[i] = keys[c];
                    i = c;
                }
                items[i] = lastItem; keys[i] = lastKey;
                return top;
            }
        }
    }
}
