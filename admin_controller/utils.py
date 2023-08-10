import os
from asgiref.sync import async_to_sync, sync_to_async
from kaif.settings import bot, ADMIN_ID, MEDIA_ROOT
from bot.models import TelegramUser
from django.core.files.uploadedfile import InMemoryUploadedFile


@async_to_sync
async def send_all(text, photo: InMemoryUploadedFile):
    if photo:
        photo = (await bot.send_photo(ADMIN_ID, open(os.path.join(MEDIA_ROOT, photo.name), 'rb'))).photo[-1].file_id

    func = bot.send_photo if photo else bot.send_message
    kwargs = {'caption': text, 'photo': photo} if photo else {'text': text}
    for user in await sync_to_async(list)(TelegramUser.objects.all()):
        try:
            await func(user.user_id, **kwargs)
        except Exception as e:
            print(str(e))
