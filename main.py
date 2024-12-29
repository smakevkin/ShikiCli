from dotenv import dotenv_values, set_key
import httpx
import time
from datetime import datetime
import locale
import os
from typing import List, Dict, Any


# Устанавливаем локаль для вывода месяца на русском
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

env_path = ".env"
config = dotenv_values(env_path)

stat ={
    1: "Запланированно.",
    2: "Смотрю",
    3: "Пересматриваю",
    4: "Просмотрено",
    5: "Отложено",
    6: "Брошено"
}

statEn={
    1: "planned",
    2: "watching",
    3: "rewatching",
    4: "completed",
    5: "on_hold",
    6: "dropped",
}

def clear_screen():
    # For Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # For macOS and Linux
    else:
        _ = os.system('clear')

def start_greet() -> None:
    """Запрашивает токен авторизации и сохраняет его в .env."""
    try:
        print("Перейдите по ссылке для токена авторизации: "
              "https://shikimori.one/oauth/authorize?client_id=tBREOF5VBKo2XdKFIk9jXeWRdOG_mt7o_ct4ZctbTRA&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&response_type=code&scope=user_rates")
        auth_code = input("Введите полученный токен: ")
        response = httpx.post(
            "https://shikimori.one/oauth/token",
            headers={"User-Agent": "ShikiCliLinux"},
            data={
                "grant_type": "authorization_code",
                "client_id": "tBREOF5VBKo2XdKFIk9jXeWRdOG_mt7o_ct4ZctbTRA",
                "client_secret": "T92R-iNkk-j2QoNsnU827ehgN-pNi35klGQNVKKpv64",
                "code": auth_code,
                "redirect_uri": "urn:ietf:wg:oauth:2.0:oob"
            }
        )
        response.raise_for_status()
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        created_at = str(data.get("created_at"))

        if not access_token or not refresh_token:
            raise ValueError("Токены не получены.")

        set_key(env_path, "access_token", access_token)
        set_key(env_path, "refresh_token", refresh_token)
        set_key(env_path, "when", created_at)
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        print(f"Ошибка при запросе токена: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

def refresh_token() -> None:
    """Обновляет токен авторизации."""
    try:
        refresh_token = config.get("refresh_token")
        if not refresh_token:
            raise ValueError("Refresh token отсутствует в конфигурации.")

        response = httpx.post(
            "https://shikimori.one/oauth/token",
            headers={"User-Agent": "ShikiCliLinux"},
            data={
                "grant_type": "refresh_token",
                "client_id": "tBREOF5VBKo2XdKFIk9jXeWRdOG_mt7o_ct4ZctbTRA",
                "client_secret": "T92R-iNkk-j2QoNsnU827ehgN-pNi35klGQNVKKpv64",
                "refresh_token": refresh_token
            }
        )
        response.raise_for_status()
        data = response.json()

        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        created_at = str(data.get("created_at"))

        if not access_token or not refresh_token:
            raise ValueError("Обновленные токены не получены.")

        set_key(env_path, "access_token", access_token)
        set_key(env_path, "refresh_token", refresh_token)
        set_key(env_path, "when", created_at)
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        print(f"Ошибка при обновлении токена: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

def search_anime(anime_name: str) -> List[Dict[str, Any]]:
    """Ищет аниме по названию и возвращает список найденных."""
    try:
        variables = {"animeName": anime_name}
        query = """
        query GetAnime($animeName: String!) {
            animes(search: $animeName, limit: 20, kind: "!special") {
                id
                name
                russian
                kind
                rating
                score
                status
                episodes
                episodesAired
                duration
                nextEpisodeAt
                genres { id name russian kind }
            }
        }
        """
        payload = {"query": query, "variables": variables}
        response = httpx.post("https://shikimori.one/api/graphql", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("animes", [])
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        print(f"Ошибка при поиске аниме: {e}")
    except KeyError as e:
        print(f"Ошибка в структуре данных ответа: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    return []

def menu(enum):
    match enum:
        case -1:
            clear_screen()
            print(f"Авторизован: {whoami()}")
            print()
            print("Выберите нужный раздел")
            print("1. Поиск аниме")
            #TODO: print("2. Онгоинги")
            #TODO: print("3. Профиль")
            print("0. Выход")
            print()
            mode=input("Раздел: ")
            print()
            menu(int(mode))
        case 0:
            exit()
        case 1:
            anime_search(False)

def anime_search(init):
    if init!=True:
        anime_name = input("Введите название аниме: ")
        clear_screen()
        global anime_list,choice
        anime_list = search_anime(anime_name)
        
        if len(anime_list)==0:
            print("По вашему запросу ничего не найдено, попробуйте снова",end='\n\n')
            menu(1)             
        
        for i in range(0,len(anime_list)):
            print(f"{i+1}. {anime_list[i]['name']}/{anime_list[i]['russian']}")
        print()
        choice = int(input("Выберите аниме: "))
        while choice>len(anime_list):
            choice = int(input("Выбрано неккоректный индекс, попробуйте еще раз: "))
    
    anime_info(anime_list[choice-1])
    
    print("Выберите действие: ")
    print("1. Посмотреть в anicli-ru")
    print("2. Поставить оценку")
    print("3. Поставить статус")
    #принт изменить количество просмотренных эпизодов
    print("0. Вернуться в меню.")
    mode = int(input("Действие: "))
    mode_menu(mode,anime_list[choice-1])
    if mode!=0:
        anime_search(True)
 
def mode_menu(mode,anime):
    match mode:
        case 1:
            anicli=f"anicli-ru --search '{anime["russian"]}'"
            os.system(anicli)
        case 0:
            menu(-1)
        case 2:
            score=-1
            print()
            while score>10 or score<=0:
                print("0. Вернуться в меню")
                score = int(input("Поставьте оценку от 1 до 10: "))
                if score ==0:
                    break
                if score>10 or score<1:
                    print("Оценка введена некорректно.")
            if score !=0:
                anime_rate_set(anime,score)
        case 3:
            status=-1
            print()
            print("0. Вернуться в меню")
            print("Выберите нужный статус.")
            for i in range(1,len(stat)+1):
                print(f"{i}. {stat[i]}")
            while status<=0 or status>6:
                status = int(input("Статус: "))
                if status == 0:
                    break
                if status>6 or status<1:
                    print("Статус введен неккоректно.")
            if status !=0:
                anime_status_set(anime,status)      

def anime_info(anime):
    types = {
        "tv": "TV-сериал",
        "movie": "Фильм",
        "ova": "OVA",
        "ona": "ONA",
        "special": "Спешл",
        "music": "Музыкальный"
    }
    status ={
        "anons": "Анонсировано",
        "ongoing": "Онгоинг",
        "released": "Вышло"
    }

    clear_screen()
    
    eps = get_user_eps(anime["id"])
    print(f"{anime['name']}/{anime['russian']}")
    print("Информация:")
    print(f"Рейтинг: {anime['rating']}")
    print(f"Тип: {types[anime['kind']]}")
    print(f"Статус: {status[anime["status"]]}")
    print(f"Эпизодов {anime["episodesAired"]}/{anime["episodes"]}")
    print(f"Просмотрено: {eps}/{anime["episodesAired"]}")
    
    if anime["episodes"]!=anime["episodesAired"]:
        dt = datetime.fromisoformat(anime["nextEpisodeAt"])
        formatted_dt = dt.strftime("%-d %b. %H:%M")
        print(f"Следующий эпизод: {formatted_dt}")
    
    genres=[]
    for i in range(0,len(anime["genres"])):
        if anime["genres"][i]["kind"]=="genre":
            genres.append(anime["genres"][i]["russian"])
    print("Жанры: ", end='')
    for i in range(0, len(genres)):
        if i == len(genres) - 1:
            print(genres[i], end='\n') 
        else:
            print(genres[i], end=', ')  

    themes=[]
    for i in range(0,len(anime["genres"])):
        if anime["genres"][i]["kind"]=="theme":
            themes.append(anime["genres"][i]["russian"])
    if len(themes)!=0:
        print("Темы: ", end='')
        for i in range(0, len(themes)):
            if i == len(genres) - 1:
                print(themes[i], end='\n') 
            else:
                print(themes[i], end=', ')  

def anime_rate_set(anime,score):
    url = "https://shikimori.one/api/v2/user_rates"
    token = f"Bearer {config['access_token']}"

    data = {
        "user_rate": {
            "user_id": config["userid"],
            "target_id": anime["id"],
            "target_type": "Anime",
            "score": score,
        }
    }

    response = httpx.post(
        url,
        headers={"Authorization": token, "User-Agent": "ShikiCliLinux"},
        json=data
    )
    if response.status_code==201:
        print(f"Оценка {score} поставлена!")

def anime_status_set(anime,status):
    url = "https://shikimori.one/api/v2/user_rates"
    token = f"Bearer {config['access_token']}"

    data = {
        "user_rate": {
            "user_id": config["userid"],
            "target_id": anime["id"],
            "target_type": "Anime",
            "status": statEn[status],
        }
    }
    response = httpx.post(
        url,
        headers={"Authorization": token, "User-Agent": "ShikiCliLinux"},
        json=data
    )

    if response.status_code==201:
        print(f"Статус {stat[status]} поставлена!")

def get_user_eps(anime):
    response = httpx.get(
        "https://shikimori.one/api/v2/user_rates",
        params={
            "user_id": config["userid"],
            "target_id": anime,
            "target_type": "Anime"
        }
    )
    if len(response.json())!=0:
        return response.json()["episodes"]
    return 0

def whoami():
    url=f"https://shikimori.one/api/users/whoami"
    token=f"Bearer {config['access_token']}"
    response = httpx.get(
        url,
        headers={"Authorization": token,"User-Agent": "ShikiCliLinux"}
    )
    set_key(env_path,"userid",str(response.json()["id"]))
    return response.json()["nickname"]

def main():
    if config["access_token"] == "" or config["refresh_token"] == "":
        start_greet()
    else:
        if int(time.time())-int(config["when"])>=86400:
            refresh_token()
    print()
    while True:
        menu(-1)
        
    
main()

