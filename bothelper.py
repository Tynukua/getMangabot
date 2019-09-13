import json
from pprint import pprint
import telethon
import asyncio
import os

API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
client = telethon.TelegramClient(f'loader-session', API_ID, API_HASH)
client.start()
PRIVATE = None

def check_entity(message):
	if message.entities:
		for entitie in message.entities:
			if 'url' in entitie:
				return entitie.url
			elif entitie.type == 'url':
				return message.text
	return None

def main_buttums(project, title):
	keyboard = json.dumps({'inline_keyboard':
				[
					[{'text':'Download', 'callback_data': f'l_b {project} {title}'}],
					[{'text':'Show vols', 'callback_data': f's_v {project} {title} 0'}],
					[{'text':'Show chapters', 'callback_data': f's_c {project} {title} 0'}] 
				]
			})
	return keyboard

def volume_keyboard(project, title, page, chapter_dict, w=2,h = 5):
	top = [[{'text':'⬆️', 'callback_data':f'main {project} {title}'}]]
	isAlone = False
	#chapter_dict = list(chapter_dict)
	volume_count = len(chapter_dict)
	if volume_count> w*h+2:
		if volume_count // (w*h) < volume_count / (w*h):
			page_count = volume_count // (w*h) +1 
		else:
			page_count = volume_count // (w*h)
		page = page_count + int(page); page%=page_count
		turner = [
			{'text':'<<',
				'callback_data':f's_v {project} {title} {page-1}'},
			{'text':'>>', 
				'callback_data':f's_v {project} {title} {page+1}'} ]
	else:
		page_count = 1
		page = 0
		isAlone = True

	buttums = [{'text':f'Volume {vol}',
		'callback_data':f'l_v {project} {title} {vol}'} 
		for vol in chapter_dict
			][	w*h*page : w*h*(page+1) if not  isAlone else None  ]

	lines = [] 
	while True:
		line = []
		for _ in range(w):
			if buttums:
				line.append(buttums.pop(0))
			else:
				if line: lines.append(line)
				break
		else:
			lines.append(line)
			continue
		break
	lines = top+lines
	if not isAlone:
		lines+= [turner]
	return json.dumps({'inline_keyboard':lines})

def chapter_keyboard(project, title, page, chapter_list, w=2,h = 5):
	top = [[{'text':'⬆️', 'callback_data':f'main {project} {title}'}]]
	isAlone = False
	chapter_count = len(chapter_list)
	if chapter_count>12:
		if chapter_count // (w*h) < chapter_count / (w*h):
			page_count = chapter_count // (w*h) +1 
		else:
			page_count = chapter_count // (w*h)
		page = page_count + int(page); page%=page_count
		turner = [
			{'text':'<<',
				'callback_data':f's_c {project} {title} {page-1}'},
			{'text':'>>', 
				'callback_data':f's_c {project} {title} {page+1}'} ]
	else:
		page_count = 1
		page = 0
		isAlone = True

	buttums = [{'text':f'V {vol}. Ch {chapter}.',
		'callback_data':f'l_c {project} {title} {vol} {chapter}'} 
		for vol,chapter,i in chapter_list
			][	w*h*page : w*h*(page+1) if not  isAlone else None  ]

	lines = [] 
	while True:
		line = []
		for _ in range(w):
			if buttums:
				line.append(buttums.pop(0))
			else:
				if line: lines.append(line)
				break
		else:
			lines.append(line)
			continue
		break
	lines = top+lines
	if not isAlone:
		lines+= [turner]
	return json.dumps({'inline_keyboard':lines})

async def send_progress(loader,bot,message):

	progress = 100-100*loader.img_list.count(None)/loader.len_list
	text = '`%.2f`' % progress
	text+='% pictures was loaded'
	if loader.img_list.count(None) ==0:
		text = '100% pictures\'ve been loaded!'
	await bot.edit_message_text(chat_id = message.chat.id, 
		message_id = message.message_id, 
		text = text, parse_mode = 'Markdown')
class TelegramSender:
	def __init__(self, path_to_file, bytes = None):
		#self.bytes = bytes
		self.path_to_file = path_to_file
		if bytes:
			with open(path_to_file,'wb') as f:
				f.write(bytes)
	async def send(self, message):
		global PRIVATE
		if not PRIVATE:
			await client.get_dialogs()
			PRIVATE = -1001213568715
		await client.send_file(PRIVATE,self.path_to_file, caption = 'send_to_user: '+ str(message.chat.id)	)

