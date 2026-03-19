from firebase_admin import messaging, exceptions

from useraccount.models import Profile


def send_firebase_notification(user_id, title, message, image_url=None):
    """
    Отправляет push-уведомление через Firebase для указанного пользователя.
    """
    try:
        # Получаем пользователя
        user = Profile.objects.get(id=user_id)
        if not user.device_token:
            print(f"Пользователь {user_id} не имеет токена устройства.")
            return {
                "success": False,
                "message": "Пользователь не имеет токена устройства",
            }

        print(
            f"Отправка уведомления пользователю {user_id} с токеном: {user.device_token}"
        )

        # Формируем уведомление
        notification = messaging.Notification(
            title=title, body=message, image=image_url
        )
        message = messaging.Message(
            notification=notification,
            token=user.device_token,
        )

        # Отправляем уведомление
        response = messaging.send(message)
        print(f"Уведомление успешно отправлено. Ответ: {response}")
        return {"success": True, "response": response}

    except Profile.DoesNotExist:
        print(f"Пользователь {user_id} не найден.")
        return {"success": False, "message": "Пользователь не найден"}
    except exceptions.FirebaseError as e:
        print(f"Ошибка Firebase: {e}")
        return {"success": False, "message": f"Ошибка Firebase: {e}"}
    except Exception as e:
        print(f"Другая ошибка: {e}")
        return {"success": False, "message": str(e)}
