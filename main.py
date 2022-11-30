import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from func import search_users, get_photo, sort_likes, json_create
from db import engine, Session, write_msg, register_user, add_user, add_user_photos, add_to_black_list, \
    check_db_user, check_db_black, check_db_favorites, check_db_master, delete_db_blacklist, delete_db_favorites
from config import group_token, user_token
import requests
from datetime import datetime


# Для работы с вк_апи
vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)
# Для работы с БД
session = Session()
connection = engine.connect()


def loop_bot():
  for this_event in longpoll.listen():
    if this_event.type == VkEventType.MESSAGE_NEW:
      if this_event.to_me:
        message_text = this_event.text
        return message_text, this_event.user_id


def menu_bot(id_num):
  write_msg(
    id_num, f"Вас приветствует бот!\n"
    f"\nЕсли вы используете его первый раз - пройдите регистрацию.\n"
    f"Для регистрации введите - Да.\n"
    f"Если Вы уже зарегистрированы - начинайте поиск.\n"
    f"\nДля поиска - ищи\n"
    f"Перейти в избранное нажмите - 2\n"
    f"Перейти в черный список - 0\n")


def show_info():
  write_msg(
    user_id, f'Это последняя анкета.'
    f'Перейти в избранное - 2'
    f'Перейти в черный список - 0'
    f'Поиск - ищи'
    f'Меню бота - Vkinder')


def reg_new_user(id_num):

    write_msg(id_num, 'Вы прошли регистрацию.')
    write_msg(id_num, 'Vkinder - для активации бота\n')

    register_user(id_num)




def go_to_favorites(ids):
  alls_users = check_db_favorites(ids)
  write_msg(ids, f'Избранные анкеты:')
  for nums, users in enumerate(alls_users):
    write_msg(ids, f'{users.first_name}, {users.second_name}, {users.link}')
    write_msg(ids, '1 - Удалить из избранного, 0 - Далее \nq - Выход')
    msg_texts, user_ids = loop_bot()
    if msg_texts == '0':
      if nums >= len(alls_users) - 1:
        write_msg(
          user_ids, f'Это последняя анкета.\n'
          f'Vkinder - вернуться в меню\n')
    # Удаляет из избранное
    elif msg_texts == '1':
      delete_db_favorites(users.vk_id)
      write_msg(user_ids, f'Анкета удалена.')
      if nums >= len(alls_users) - 1:
        write_msg(
          user_ids, f'Это последняя анкета.\n'
          f'Vkinder - вернуться в меню\n')
    elif msg_texts.lower() == 'q':
      write_msg(ids, 'Vkinder - для активации бота.')
      break
    else:
      input_error()
      break


def go_to_blacklist(ids):
  all_users = check_db_black(ids)
  write_msg(ids, f'Анкеты в черном списке:')
  for num, user in enumerate(all_users):
    write_msg(ids, f'{user.first_name}, {user.second_name}, {user.link}')
    write_msg(ids, '1 - Удалить из черного списка, 0 - Далее \nq - Выход')
    msg_texts, user_ids = loop_bot()
    if msg_texts == '0':
      if num >= len(all_users) - 1:
        write_msg(
          user_ids, f'Это последняя анкета.\n'
          f'Vkinder - вернуться в меню\n')
    # Удаляет из черный список
    elif msg_texts == '1':
      print(users.id)
      delete_db_blacklist(users.vk_id)
      write_msg(user_ids, f'Анкета успешно удалена.')
      if num >= len(all_users) - 1:
        write_msg(
          user_ids, f'Это последняя анкета.\n'
          f'Vkinder - вернуться в меню\n')
    elif msg_texts.lower() == 'q':
      write_msg(ids, 'Vkinder - для активации бота.')
      break
    else:
      input_error()
      break


# Собирает инфо о пользователе для поиска пары
def search_info(user_id):

  url = 'https://api.vk.com/method/users.get'
  params = {'user_ids': user_id, 'fields': 'bdate,sex,city',
            'access_token': user_token,
            'v': '5.131'}
  res = requests.get(url, params=params)

  json_res = res.json()
  try:
    if 'bdate' in json_res['response'][0].keys() and \
          len(json_res['response'][0]['bdate']) > 7:
      age_bot_user = int(json_res['response'][0]['bdate'][-4:])
      age_to = (int(datetime.now().year) - age_bot_user) + 3
      age_at = (int(datetime.now().year) - age_bot_user) - 3

    else:
      write_msg(user_id, 'Возраст от:')
      msg_text, user_id = loop_bot()
      age_to = msg_text[0:1]
      write_msg(user_id, 'Возраст до:')
      msg_text, user_id = loop_bot()
      age_at = msg_text[0:1]
  # print(json_res)

    sex_user = json_res['response'][0]['sex']
    if sex_user == 1:
      sex = 2
    elif sex_user == 2:
      sex = 1

    else:
      write_msg(user_id, 'Введите пол.\n1 - девушка\n2 - парень')
      msg_text, user_id = loop_bot()
      sex = msg_text[0:1]

    if 'city' in json_res['response'][0]:
      city = json_res['response'][0]['city']['title']

    else:
      write_msg(user_id, 'Введите город')
      msg_text, user_id = loop_bot()
      city = msg_text[0:len(msg_text)].lower()



    return sex, age_to, age_at, city
  except KeyError:
    write_msg(user_id, 'Ошибка получения токена.')

def input_error():
  write_msg(user_id, 'Не понимаю вас.'
            '\nVkinder - для активации бота.')

if __name__ == '__main__':
  while True:
    msg_text, user_id = loop_bot()

    if msg_text[0:7].lower() == 'vkinder':
      menu_bot(user_id)
      msg_text, user_id = loop_bot()

      # Регистрирует пользователя в БД
      if msg_text.lower() == 'да':
        current_user_id = check_db_master(user_id)
        if current_user_id:
          write_msg(user_id, 'уже зареган пиши вкиндер')
        else:
          reg_new_user(user_id)





      # Ищет партнера
      # elif len(msg_text) > 1:
      #   sex = 0
      elif msg_text[0:3].lower() == 'ищи':
        try:
          sex, age_to, age_at, city = search_info(user_id)

        # if msg_text[0:7].lower() == 'девушка':
        #   sex = 1
        # elif msg_text[0:7].lower() == 'мужчина':
        #   sex = 2
        # age_at = msg_text[8:10]
        # if int(age_at) < 18:
        #   write_msg(user_id, 'Выставлен минимальный возраст - 18 лет.')
        #   age_at = 18
        # age_to = msg_text[11:14]
        # if int(age_to) >= 100:
        #   write_msg(user_id, 'Выставлено максимальное значение - 99 лет.')
        #   age_to = 99
        # city = msg_text[14:len(msg_text)].lower()

          # Ищет анкеты
          result = search_users(sex, int(age_at), int(age_to), city)
          json_create(result)
          current_user_id = check_db_master(user_id)
          # Отбирает анкеты
          for i in range(len(result)):
            dating_user, blocked_user = check_db_user(result[i][3])
            # Получает фото и сортирует по лайкам
            user_photo = get_photo(result[i][3])
            if user_photo == 'нет доступа к фото' or dating_user is not None or blocked_user is not None:
              continue
            sorted_user_photo = sort_likes(user_photo)
            # Выводит отсортированные данные по анкетам
            write_msg(
              user_id,
              f'\n{result[i][0]}  {result[i][1]}  {result[i][2]}',
            )
            try:
              write_msg(user_id,
                          f'фото:',
                          attachment=','.join([
                            sorted_user_photo[-1][1], sorted_user_photo[-2][1],
                            sorted_user_photo[-3][1]
                          ]))
            except IndexError:
              for photo in range(len(sorted_user_photo)):
                write_msg(user_id,
                            f'фото:',
                            attachment=sorted_user_photo[photo][1])
            # Ждет ввод
            write_msg(
              user_id,
              '1 - Добавить, 2 - Заблокировать, 0 - Далее, \nq - выход из поиска'
            )
            msg_text, user_id = loop_bot()
            if msg_text == '0':
              # Проверка на последнюю запись
              if i >= len(result) - 1:
                show_info()
            # Добавляет пользователя в избранное
            elif msg_text == '1':
              # Проверка на последнюю запись
              if i >= len(result) - 1:
                show_info()
                break
              # Добавляет анкету в БД
              try:
                add_user(user_id, result[i][3], result[i][1], result[i][0], city,
                           result[i][2], current_user_id.id)
                # Добавляет фото в БД
                add_user_photos(user_id, sorted_user_photo[0][1],
                                  sorted_user_photo[0][0], current_user_id.id)
              except AttributeError:
                write_msg(
                  user_id,
                  'Вы не зарегистрировались!\n Введите Vkinder для перезагрузки бота'
                )
                break
            # Добавляет пользователя в черный список
            elif msg_text == '2':
              # Проверка на последнюю запись
              if i >= len(result) - 1:
                show_info()
              # Блокирует
              add_to_black_list(user_id, result[i][3], result[i][1],
                                  result[i][0], city, result[i][2],
                                  sorted_user_photo[0][1], sorted_user_photo[0][0],
                                  current_user_id.id)
            elif msg_text.lower() == 'q':
              write_msg(user_id, 'До встречи.')
              break
            else:
              input_error()
              break
        except Exception:
          write_msg(user_id, 'Что-то пошло не так.'
                    '\nVkinder - для активации бота.')

      # Переходит в избранное
      elif msg_text == '2':
        go_to_favorites(user_id)

      # Переходимт в черный список
      elif msg_text == '0':
        go_to_blacklist(user_id)

      else:
        input_error()

    elif len(msg_text) > 0:
      write_msg(user_id, f'Здравствуйте! '
                         f'\nВведите Vkinder для активации бота.')



