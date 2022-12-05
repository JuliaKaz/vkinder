import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import sqlalchemy
from random import randrange
import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy_utils import database_exists, create_database
from config import group_token


# Для работы с вк_апи
vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)

#База
Base = declarative_base()
engine = sq.create_engine('postgresql://postgres:(пароль)@localhost:5432/vkbot_jul',
                          client_encoding='utf8')

if not database_exists(engine.url):
  create_database(engine.url)
  print('База данных создана...')

Session = sessionmaker(bind=engine)
session = Session()
engine.connect()
connection = engine.connect()


class User(Base):
  __tablename__ = 'users'
  id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
  vk_id = sq.Column(sq.Integer, unique=True)


# Анкеты добавленные в избранное
class DatingUser(Base):
  __tablename__ = 'dating_user'
  id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
  vk_id = sq.Column(sq.Integer, unique=True)
  first_name = sq.Column(sq.String)
  second_name = sq.Column(sq.String)
  city = sq.Column(sq.String)
  link = sq.Column(sq.String)
  id_user = sq.Column(sq.Integer, sq.ForeignKey('users.id', ondelete='CASCADE'))


# Фото избранных анкет
class Photos(Base):
  __tablename__ = 'photos'
  id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
  link_photo = sq.Column(sq.String)
  count_likes = sq.Column(sq.Integer)
  id_dating_user = sq.Column(
    sq.Integer, sq.ForeignKey('dating_user.id', ondelete='CASCADE'))


# Анкеты в черном списке
class BlackList(Base):
  __tablename__ = 'black_list'
  id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
  vk_id = sq.Column(sq.Integer, unique=True)
  first_name = sq.Column(sq.String)
  second_name = sq.Column(sq.String)
  city = sq.Column(sq.String)
  link = sq.Column(sq.String)
  link_photo = sq.Column(sq.String)
  count_likes = sq.Column(sq.Integer)
  id_user = sq.Column(sq.Integer, sq.ForeignKey('users.id', ondelete='CASCADE'))


# Пишет сообщение пользователю
def write_msg(user_id, message, attachment=None):
  vk.method(
      'messages.send', {
      'user_id': user_id,
      'message': message,
      'random_id': randrange(10**7),
      'attachment': attachment
    })


# Регистрация пользователя
def register_user(vk_id):
    new_user = User(vk_id=vk_id)
    session.add(new_user)
    session.commit()
    return True


# Удаляет пользователя из черного списка
def delete_db_blacklist(ids):
  current_user = session.query(BlackList).filter_by(vk_id=ids).first()
  session.delete(current_user)
  session.commit()


# Удаляет пользователя из избранного
def delete_db_favorites(ids):
  current_user = session.query(DatingUser).filter_by(vk_id=ids).first()
  session.delete(current_user)
  session.commit()


# Проверят регистрацию пользователя в БД
def check_db_master(ids):
  current_user_id = session.query(User).filter_by(vk_id=ids).first()
  return current_user_id


# Проверят есть ли юзер в бд
def check_db_user(ids):
  dating_user = session.query(DatingUser).filter_by(vk_id=ids).first()
  blocked_user = session.query(BlackList).filter_by(vk_id=ids).first()
  return dating_user, blocked_user


# Проверят есть ли юзер в черном списке
def check_db_black(ids):
  current_users_id = session.query(User).filter_by(vk_id=ids).first()
  # Находит анкеты из черного списка, добавленные юзером
  all_users = session.query(BlackList).filter_by(
    id_user=current_users_id.id).all()
  return all_users


# Проверяет есть ли юзер в избранном
def check_db_favorites(ids):
  current_users_id = session.query(User).filter_by(vk_id=ids).first()
  # Находит все анкеты из избранного, добавленные юзером
  alls_users = session.query(DatingUser).filter_by(
    id_user=current_users_id.id).all()
  return alls_users


# Сохраняет избранного пользователя в БД
def add_user(event_id, vk_id, first_name, second_name, city, link, id_user):
  try:
    new_user = DatingUser(vk_id=vk_id,
                          first_name=first_name,
                          second_name=second_name,
                          city=city,
                          link=link,
                          id_user=id_user)
    session.add(new_user)
    session.commit()
    write_msg(event_id, 'Пользователь добавлен в избранное.')
    return True
  except (IntegrityError, InvalidRequestError):
    write_msg(event_id, 'Пользователь уже в избранном.')
    return False


# Сохранение в БД фото добавленного пользователя
def add_user_photos(event_id, link_photo, count_likes, id_dating_user):
  try:
    new_user = Photos(link_photo=link_photo,
                      count_likes=count_likes,
                      id_dating_user=id_dating_user)
    session.add(new_user)
    session.commit()
    write_msg(event_id, 'Фото пользователя сохранено в избранном.')
    return True
  except (IntegrityError, InvalidRequestError):
    write_msg(event_id,
              'Невозможно добавить фото этого пользователя(Уже сохранено).')
    return False


# Добавление пользователя в черный список
def add_to_black_list(event_id, vk_id, first_name, second_name, city, link,
                      link_photo, count_likes, id_user):
  try:
    new_user = BlackList(vk_id=vk_id,
                         first_name=first_name,
                         second_name=second_name,
                         city=city,
                         link=link,
                         link_photo=link_photo,
                         count_likes=count_likes,
                         id_user=id_user)
    session.add(new_user)
    session.commit()
    write_msg(event_id, 'Пользователь успешно заблокирован.')
    return True
  except (IntegrityError, InvalidRequestError):
    write_msg(event_id, 'Пользователь уже в черном списке.')
    return False


if __name__ == '__main__':
    Base.metadata.create_all(engine)
