import os
import asyncio
import aiohttp
import getManga
from aiogram import Bot, Dispatcher, executor, types
from aiohttp import web, request
from getManga import Manga, ImgListPDF
from bothelper import check_entity, chapter_keyboard, main_buttums, volume_keyboard, send_progress, TelegramSender
from pprint import pprint

ADMIN = 382572750
TOKEN =  os.environ.get('API_TOKEN')
WEBHOOK = os.environ.get('HOST')
#PROXY = '199.21.96.73:80'
PRIVATE = -1001213568715
WELCOME = '''Konnichiwa, {}!

I can download in PDF format from different websites!
Now you can send me link from following websites:

● mangalib.me [RUS]
● mangarock.com [ENG]
'''
HELP = '''1. Send link from supported websites
2. Choose volume or chapter
3. Enjoy it!'''
routes = web.RouteTableDef()
bot = Bot(token=TOKEN, timeout=60)
dp = Dispatcher(bot)

manga_session = {}    

@routes.post(f'/{TOKEN}')
async def getUpdate(request):
    asyncio.create_task(dp.updates_handler.notify(types.Update(**(await request.json()))))
    return web.Response(text="OK")
@routes.get(f'/')
async def reset_hooks(app):
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK+TOKEN)
    return web.Response(text="OK")

app = web.Application()
app.add_routes(routes)


@dp.message_handler(regexp = '/start')
async def start(message: types.Message):
    await bot.send_message(message.chat.id, WELCOME.format(message.from_user.first_name))

@dp.message_handler(regexp = '/help')
async def help(message: types.Message):
    await bot.send_message(message.chat.id, HELP)

@dp.channel_post_handler(text_contains = 'send_to_user:', content_types = ['document'])
async def load_file(message):
    if message.chat.id == PRIVATE:
        _cmd, user_id = message.caption.split()
        await bot.send_document(int(user_id), message.document.file_id, caption = message.document.file_name[:-4])

@dp.callback_query_handler(text_contains="s_c")
async def show_chapters(call):
    _cmd, project, title, page  = call.data.split()
    manga = manga_session.get((project, title)) if (project, title) in manga_session else Manga.get(project, title)
    manga_session.update({(project, title):manga})
    
    keyboard = chapter_keyboard(project, title, page, manga.chapter_list)
    await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,     
            reply_markup = keyboard )

@dp.callback_query_handler(text_contains="main")
async def main_keyboard(call):
    _cmd, project, title = call.data.split()
    await bot.edit_message_reply_markup(call.message.chat.id, 
        call.message.message_id,     
        reply_markup = main_buttums(project, title))

@dp.callback_query_handler(text_contains="s_v")
async def show_volumes(call):
    _cmd, project, title, page  = call.data.split()
    manga = manga_session.get((project, title)) if (project, title) in manga_session else Manga.get(project, title)
    manga_session.update({(project, title):manga})

    keyboard = volume_keyboard(project, 
            title, 
            page, 
            manga.chapter_dict)
    await bot.edit_message_reply_markup(call.message.chat.id, 
        call.message.message_id, 
        reply_markup = keyboard )    

@dp.callback_query_handler(text_contains="l_c")
async def load_chapter(call):
    _cmd, project, title, vol, chapter  = call.data.split()
    manga = manga_session.get((project, title)) if (project, title) in manga_session else Manga.get(project, title)
    manga_session.update({(project, title):manga})
    message = await bot.send_message(call.message.chat.id,'Loading\'s been started!')
    chapter_obj = manga.get_chapter(chapter)    
    link_list = chapter_obj.img_list
    loader = ImgListPDF(link_list, 
        f'./{project}/{title}/v{vol}-c{chapter}', 
        send_progress, 
        (bot, message) )
    await loader.aload_all()
    await bot.delete_message(chat_id =message.chat.id, message_id = message.message_id)
    book = TelegramSender(f'./{project}/{title}/v{vol}-c{chapter}/{title}_v{vol}_c{chapter}.pdf',
        loader.pdfbyte)
    await book.send(message)


@dp.callback_query_handler(text_contains="l_v")
async def load_vol(call):
    _cmd, project, title, vol  = call.data.split()
    manga = manga_session.get((project, title)) if (project, title) in manga_session else Manga.get(project, title)
    manga_session.update({(project, title):manga})
    message = await bot.send_message(call.message.chat.id,'Loading\'s been started!')
    volume_obj = manga.get_volume(vol)
    link_list = volume_obj.img_list
    loader = ImgListPDF(link_list, 
        f'./{project}/{title}/v{vol}', 
        send_progress, 
        (bot, message) )
    await loader.aload_all()
    await bot.delete_message(chat_id =message.chat.id, message_id = message.message_id)
    book = TelegramSender(f'./{project}/{title}/v{vol}/{title}_v{vol}.pdf',
        loader.pdfbyte)
    await book.send(message)
@dp.callback_query_handler(text_contains="l_b")
async def coming_soon(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id, 'Coming soon...')

@dp.message_handler(lambda message:check_entity(message) )
async def link(message: types.Message):
    url = check_entity(message)
    print(url)
    try: manga = Manga(url)
        
    except Exception as ex:
        await bot.forward_message(ADMIN, from_chat_id = message.chat.id, message_id = message.message_id)
        await bot.send_message(ADMIN, f'`{str(ex)}`', parse_mode = 'Markdown')
        try:
            await bot.send_sticker(message.chat.id,
                'CAADAgADpgQAApIKKUt4ZtMRaeSStxYE')
        except Exception as ex:
            await bot .send_message(ADMIN, str(ex)) 
            with open('wrong_link.webp','rb') as sticker_file:
                await bot.send_sticker(message.chat.id, sticker_file.read()) 
        return
    manga_session.update({(manga.site, manga.title): manga})
    pprint(manga.info)
    keyboard = main_buttums(
            manga.site,
            manga.title )
    print(keyboard)
    await bot.send_photo(
        message.chat.id,
        manga.cover,
        caption = f'''*{manga.name} {manga.lang}*
{manga.description}
`Last volume:` {manga.last_volume}
`Last chapter:` {manga.last_chapter}''',
        parse_mode = 'Markdown',
        reply_markup = main_buttums(
            manga.site,
            manga.title))
    
@dp.message_handler()
async def unknown_message_handler(message: types.Message):
    await bot.forward_message(ADMIN, from_chat_id = message.chat.id, message_id = message.message_id)
if __name__ == '__main__':
    #executor.start_polling(dp, skip_updates=True)
    web.run_app(app, host = '0.0.0.0', port = int(os.environ.get('PORT', 5000)))
