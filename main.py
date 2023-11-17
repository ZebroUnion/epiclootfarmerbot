import requests
import random
import time
import datetime

class API:
    def __init__(self, cookies_path:str=None, debug:bool=False):
        self.uri = "https://epicloot.in/api/"
        self.debug = debug
        with open(cookies_path, "r") as f:
            self.cookies = f.read()
            f.close()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
            "Referer": "https://epicloot.in/",
            "Cookie": self.cookies,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "TE": "trailers"
        }

    def post(self, uri:str, headers:dict, json:dict={}):
        req = requests.post(self.uri + uri, headers=headers, json=json)
        if self.debug:
            print(str(req.json())+'\n')
        return req
    
    def get(self, uri:str, headers:dict):
        req = requests.get(self.uri + uri, headers=headers)
        if self.debug:
            print(str(req.json())+'\n')
        return req

    def refresh_cookies(self, cookies_path:str):
        with open(cookies_path, "r") as f:
            self.cookies = f.read()
            f.close()
        self.headers["Cookie"] = self.cookies

    def profile(self, uid:int):
        return self.get(f"user/{uid}", headers=self.headers)

    def active_promo(self, promo:str):
        return self.post(f"event/sm/promo", headers=self.headers, json={"promo": promo})

    def get_game_pass(self):
        return self.post(f"event/sm/getFree", headers=self.headers)

    def get_my_gifts(self, page: int=None):
        r = self.get(f"event/sm/myGifts", headers=self.headers)
        if page is None:
            page = r.json()['total']
        return self.get(f"event/sm/myGifts?page={page}", headers=self.headers)

    def get_event_status(self):
        return self.get("event", headers=self.headers)


class Game():
    def __init__(self, api):
        self.api = api
        self.game_id = None
        self.status = None
        self.ended = None
        self.lives_left = None
        self.steps_taken = None
        self.prize = None

    def start(self):
        req = self.api.post("event/game/start", headers=self.api.headers)
        if req.status_code != 200 or req.json()['success'] is False:
            return req
        self.game_id = req.json()["id"]
        self.ended = False
        self.status = 'Playing'
        self.lives_left = req.json()["lives"]
        self.steps_taken = 1
        return req

    def make_step(self):
        y_step = random.choice(range(1,4))
        req = self.api.post(f"event/game/move", headers=self.api.headers, json={"id": self.game_id, "x": self.steps_taken, "y": y_step})
        rt = 0
        while req.json()['success'] is False and rt < 5:
            req = self.api.post(f"event/game/move", headers=self.api.headers, json={"id": self.game_id, "x": self.steps_taken, "y": y_step})
            time.sleep(1)
            rt += 1
        if req.status_code != 200 or req.json()['success'] is False:
            return req, y_step
        if req.json()['dead'] is True:
            self.lives_left -= 1
            self.steps_taken = 1
            return req, y_step
        if req.json()['lives'] == 0:
            self.ended = True
            self.status = 'Lost'
            return req, y_step
        self.steps_taken += 1
        if self.steps_taken == 6:
            self.ended = True
            self.status = 'Won'
            self.prize = req.json()['gift']
            return req, y_step
        return req, y_step

    def play(self):
        g = self.start()
        if g.json()['success'] is False:
            print(g.json())
            return
        print('Начал игру #', self.game_id)
        while not self.ended:
            step, y_step = self.make_step()
            if step.json()['success'] is False:
                print(f'Ошибка {step.json()}')
                break
            print('Сделал шаг на x: '+str(self.steps_taken)+' y:'+str(y_step)+f' | {"Умер" if step.json()["dead"] == True else "Живой"}')
            time.sleep(1.2)
        print(f'Игра окончена | {"Проигрыш" if self.status == "Lost" else "Победа"}')
        print(f'Приз: {self.prize}')
        return True


    def define_prize_future(self, gift):
        good_gifts = ['карта сокровищ', 'Аркана', 'скин', 'кейс', 'ЭПИК КОИНОВ']
        if gift.json()['title'].__contains__(good_gifts):
            return True
        return False



class Farmer(API):
    pass

if __name__ == "__main__":
    a = API(cookies_path="./cookies.txt", debug=True)
    while True:
        t = a.get_game_pass()
        if t.json()['success'] is True:
            print('Получил билет')
        tickets = int(a.get_event_status().json()['summer']['user']['tries'])
        while tickets != 0:
           Game(a).play()
           tickets = int(a.get_event_status().json()['summer']['user']['tries'])
        tts = int(a.get_event_status().json()['summer']['user']['countdown'])
        print(f'Жду {round(tts / 60)} минут')
        time.sleep(tts)