import random
import json
from typing import Dict, List
from fastapi import WebSocket

class ChallengeManager:
    def __init__(self):
        # active_rooms[room_code] = {
        #   "status": "waiting" | "playing" | "finished",
        #   "questions": [{"q": "5 + 7", "a": 12}, ...],
        #   "players": {
        #       student_id: {
        #           "websocket": WebSocket,
        #           "name": "Juan",
        #           "score": 0,
        #           "current_q": 0,
        #           "finished": False
        #       }
        #   }
        # }
        self.active_rooms: Dict[str, dict] = {}

    def _generate_questions(self, count: int = 5) -> List[dict]:
        questions = []
        for _ in range(count):
            op = random.choice(['+', '-', '*'])
            a = random.randint(1, 10 if op == '*' else 20)
            b = random.randint(1, 10 if op == '*' else 20)
            
            # Avoid negative answers for basic level
            if op == '-' and a < b:
                a, b = b, a
                
            q_text = f"{a} {op} {b}"
            ans = eval(q_text)
            questions.append({"q": q_text, "a": ans})
        return questions

    async def connect(self, websocket: WebSocket, room_code: str, student_id: str, student_name: str):
        await websocket.accept()

        if room_code not in self.active_rooms:
            self.active_rooms[room_code] = {
                "status": "waiting",
                "questions": self._generate_questions(),
                "players": {}
            }

        room = self.active_rooms[room_code]

        if room["status"] != "waiting":
            await websocket.send_json({"type": "error", "message": "La sala ya está en juego o finalizó."})
            await websocket.close()
            return False

        room["players"][student_id] = {
            "websocket": websocket,
            "name": student_name,
            "score": 0,
            "current_q": 0,
            "finished": False
        }

        # Broadcast who's waiting
        await self._broadcast_lobby(room_code)

        # Auto-start if 2 players reached (or you can adjust logic to wait for more)
        if len(room["players"]) >= 2:
            room["status"] = "playing"
            await self._start_game(room_code)
            
        return True

    def disconnect(self, room_code: str, student_id: str):
        if room_code in self.active_rooms:
            if student_id in self.active_rooms[room_code]["players"]:
                del self.active_rooms[room_code]["players"][student_id]
            
            # Clean up empty rooms
            if not self.active_rooms[room_code]["players"]:
                del self.active_rooms[room_code]

    async def broadcast(self, room_code: str, message: dict):
        if room_code in self.active_rooms:
            for player in self.active_rooms[room_code]["players"].values():
                try:
                    await player["websocket"].send_json(message)
                except Exception:
                    pass

    async def _broadcast_lobby(self, room_code: str):
        if room_code not in self.active_rooms: return
        players_info = [{"name": p["name"]} for p in self.active_rooms[room_code]["players"].values()]
        await self.broadcast(room_code, {
            "type": "player_joined",
            "players": players_info,
            "message": "Esperando más jugadores..."
        })

    async def _start_game(self, room_code: str):
        if room_code not in self.active_rooms: return
        room = self.active_rooms[room_code]
        
        # Send initial state individually so they get their own first question
        for s_id, player in room["players"].items():
            first_q = room["questions"][0]["q"]
            await player["websocket"].send_json({
                "type": "game_start",
                "question": first_q,
                "question_index": 1,
                "total_questions": len(room["questions"])
            })
            
        await self._broadcast_leaderboard(room_code)

    async def _broadcast_leaderboard(self, room_code: str):
        if room_code not in self.active_rooms: return
        room = self.active_rooms[room_code]
        
        leaderboard = [
            {"name": p["name"], "score": p["score"], "finished": p["finished"]}
            for p in room["players"].values()
        ]
        # Sort desc by score
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        
        await self.broadcast(room_code, {
            "type": "leaderboard_update",
            "leaderboard": leaderboard
        })

    async def submit_answer(self, room_code: str, student_id: str, answer: int):
        if room_code not in self.active_rooms: return
        room = self.active_rooms[room_code]
        player = room["players"].get(student_id)
        
        if not player or player["finished"] or room["status"] != "playing":
            return

        q_idx = player["current_q"]
        correct_answer = room["questions"][q_idx]["a"]

        if answer == correct_answer:
            player["score"] += 100
            player["current_q"] += 1
            
            # Check if they finished
            if player["current_q"] >= len(room["questions"]):
                player["finished"] = True
                await player["websocket"].send_json({"type": "waiting_others", "message": "¡Terminaste! Esperando a los demás..."})
            else:
                # Send next question
                next_q = room["questions"][player["current_q"]]["q"]
                await player["websocket"].send_json({
                    "type": "next_question",
                    "question": next_q,
                    "question_index": player["current_q"] + 1,
                    "total_questions": len(room["questions"])
                })
                
            await self._broadcast_leaderboard(room_code)
            await self._check_game_over(room_code)
        else:
            # Optionally deduct points or just send incorrect feedback
            await player["websocket"].send_json({"type": "feedback", "correct": False})

    async def _check_game_over(self, room_code: str):
        room = self.active_rooms[room_code]
        all_finished = all(p["finished"] for p in room["players"].values())
        
        if all_finished:
            room["status"] = "finished"
            leaderboard = [
                {"name": p["name"], "score": p["score"]}
                for p in room["players"].values()
            ]
            leaderboard.sort(key=lambda x: x["score"], reverse=True)
            winner = leaderboard[0]["name"] if leaderboard else "Empate"
            
            await self.broadcast(room_code, {
                "type": "game_over",
                "winner": winner,
                "leaderboard": leaderboard
            })
            
            # Clean up room after game over
            # self.active_rooms.pop(room_code, None) # Optional: keep it or delete it immediately

manager = ChallengeManager()
