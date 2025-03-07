import json
import os
from aformatter import format_all_entries, per_line_entries
import traceback

IS_DEPLOY_PREVIEW = False

if os.getenv('NETLIFY') == 'true' and os.getenv('CONTEXT') == 'deploy-preview':
	IS_DEPLOY_PREVIEW = True

out_ids = []
atlas_ids = {}
authors = []

while not os.path.exists('README.md'):
	os.chdir('..')

with open('web/all-authors.txt', 'r', encoding='utf-8') as authors_file:
	authors = authors_file.read().strip().split()

with open('data/read-ids.txt', 'r', encoding='utf-8') as ids_file:
	out_ids = ids_file.read().strip().split()

with open('web/atlas.json', 'r', encoding='utf-8') as atlas_file:
	atlas_data = json.loads(atlas_file.read())

last_id = 0

if not IS_DEPLOY_PREVIEW:
	for i, entry in enumerate(atlas_data):
		atlas_ids[entry['id']] = i
		id = entry['id']
		if type(id) is str and id.isnumeric():
			id = id.isnumeric()
		if type(id) is int and id > last_id and id - last_id < 100:
			last_id = int(id)

patches_dir = "data/patches/"
permanent_patch_file = "tools/temp-atlas.json"
if not os.path.exists(patches_dir):
	print("Patches folder not found. Exiting.")
	exit()

base_image_path = os.path.join('web', '_img', 'canvas', 'place30')

filenames = os.listdir(patches_dir)
filenames.append(permanent_patch_file)

controversial_entries = set([
	696, # lturepublic
	1730, 2044, # Atatürk
	2587, # Falklands War memorial
	2955, # Lola
])
edited_controversial_entries = set()

for filename in filenames:
	is_permanent_file = filename == permanent_patch_file
	if is_permanent_file:
		f = filename
	else:
		f = os.path.join(patches_dir, filename)

	print(f"{filename}: Processing...")
	
	if not os.path.isfile(f) or not f.endswith('json'):
		continue

	try:
		with open(f, 'r', encoding='utf-8') as entry_file:
			entries = json.loads(entry_file.read())
			if not isinstance(entries, list):
				entries = [entries]

			format_all_entries(entries)
			
			for entry in entries:
				if entry is None:
					continue
				if '_reddit_id' in entry:
					reddit_id = entry['_reddit_id']
					if reddit_id in out_ids:
						print(f"{filename}: Submission from {entry['id']} has been included! This will be ignored from the merge.")
						continue
					out_ids.append(reddit_id)
					del entry['_reddit_id']

				# This wouldn't work if it is an edit.
				# If needed, we can add a type to the patch to be more foolproof.
				# if entry['id'] in out_ids:
				# 	print(f"{filename}: Submission from {entry['id']} has been included! This will be ignored from the merge.")
				# 	continue

				if '_author' in entry:
					author = entry['_author']
					if author not in authors:
						authors.append(author)
					del entry['_author']

				if isinstance(entry['id'], int) and entry['id'] < 1 or entry['id'] == '0':
					if IS_DEPLOY_PREVIEW:
						last_id -= 1
					else:
						last_id += 1
					print(f"{filename}: Entry is new, assigned ID {last_id}")
					entry['id'] = last_id
				elif isinstance(entry['id'], str) and entry['id'].isnumeric():
					entry['id'] = int(entry['id'])
				elif not is_permanent_file and type(entry['id']) is str and len(entry['id']) > 5 and entry['id'] not in out_ids:
					out_ids.append(entry['id'])

				if entry['id'] in atlas_ids:
					index = atlas_ids[entry['id']]
					print(f"{filename}: Edited {atlas_data[index]['id']}.")
					atlas_data[index] = entry
					if entry['id'] in controversial_entries:
						edited_controversial_entries.add(entry['id'])
				else:
					print(f"{filename}: Added {entry['id']}.")
					atlas_data.append(entry)

		if not is_permanent_file:
			os.remove(f)

	except:
		print(f"{filename}: Something went wrong; patch couldn't be implemented. Skipping.")
		traceback.print_exc()

print('Writing...')
with open('web/atlas.json', 'w', encoding='utf-8') as atlas_file:
	per_line_entries(atlas_data, atlas_file)

with open('data/read-ids.txt', 'w', encoding='utf-8') as ids_file:
	ids_file.write("\n".join(out_ids) + "\n")

with open('web/all-authors.txt', 'w', encoding='utf-8') as authors_file:
	authors_file.write("\n".join(authors) + "\n")

print('All done.')

if len(edited_controversial_entries) > 0:
	print(f'Controversial entries edited: {edited_controversial_entries}. Inspect these manually for inappropriate content.')
