import json
from pathlib import Path

source = Path('.') / 'data.json'

src = json.loads(source.read_bytes())
output = []
for key, values in src.items():
	output.append(
		{
			"matcher": {
				'type': 'keyword',
				'keyword': key
			},
			'reply': [
				{
					'type': 'text',
					'text': value
				}
				for value in values
			]
		}
	)
	
with open('output.json', 'w', encoding='utf-8') as w:
	w.write(json.dumps(output, indent=2))
