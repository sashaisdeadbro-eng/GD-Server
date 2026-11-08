import asyncio
import websockets
import json
import os

# Словарь для хранения подключенных игроков: {websocket: {"x": 100, "y": 100, "color": "green"}}
players = {}

async def handle_connection(websocket):
    try:
        # При подключении добавляем игрока со стартовой позицией
        player_id = str(id(websocket))
        players[websocket] = {"id": player_id, "x": 200, "y": 300, "color": "green"}
        print(f"Игрок {player_id} подключился. Всего: {len(players)}")

        # Отправляем новому игроку список всех текущих игроков
        await websocket.send(json.dumps({"type": "init", "players": list(players.values())}))

        async for message in websocket:
            data = json.loads(message)
            
            # Обновляем данные игрока (позицию)
            if data["type"] == "move":
                players[websocket]["x"] = data["x"]
                players[websocket]["y"] = data["y"]
                
                # Рассылаем обновление всем остальным игрокам
                for client in players:
                    if client != websocket:
                        await client.send(json.dumps({
                            "type": "update",
                            "id": player_id,
                            "x": data["x"],
                            "y": data["y"]
                        }))

    except websockets.exceptions.ConnectionClosed:
        print(f"Игрок {player_id} отключился.")
    finally:
        # Удаляем игрока при отключении и сообщаем остальным
        if websocket in players:
            del players[websocket]
            for client in players:
                await client.send(json.dumps({"type": "remove", "id": player_id}))

async def main():
    # Хостинги передают порт через переменную окружения PORT
    port = int(os.environ.get("PORT", 8765))
    async with websockets.serve(handle_connection, "0.0.0.0", port) as server:
        print(f"Сервер запущен на порту {port}")
        await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())