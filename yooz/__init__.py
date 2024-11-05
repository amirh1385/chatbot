import re
import random

class YoozParser:
    def __init__(self):
        self.input_data_string = None
        self.patterns = []
        self.definitions = {}
        self.stop_words = []
        self.keywords = []
        self.temp_vars = {}
        self.collections = {}
        self.collection_patterns = {}
        self.last_matched_pattern = None  # متغیر برای ذخیره آخرین الگو

    def parse(self, input_data):
        self.discover_collections(input_data)
        self.input_data_string = input_data
        
        # تعریف الگوها
        definition_regex = r"#(\S+)\s*:\s*(.*?)\s*\."
        for match in re.finditer(definition_regex, input_data, re.DOTALL):
            key = match.group(1).strip()
            value = match.group(2).strip()
            self.definitions[key] = value

        # الگوی الگوها و پاسخ‌های ربات
        pattern_regex = r"\(\s*\+\s*(.*?)\s*-\s*(.*?)\s*\)"
        for match in re.finditer(pattern_regex, input_data, re.DOTALL):
            user_pattern = match.group(1).strip()
            bot_responses = [response.strip() for response in match.group(2).split('_')]
            if user_pattern.startswith('{'):
                keywords = [keyword.strip() for keyword in user_pattern[1:-1].split('،')]
                self.keywords.append({'keywords': keywords, 'bot_responses': bot_responses})
            else:
                self.patterns.append({'user_pattern': user_pattern, 'bot_responses': bot_responses})

        # الگوی کلمات توقف
        stop_words_regex = r"-\s*\{\s*(.*?)\s*\}"
        for match in re.finditer(stop_words_regex, input_data, re.DOTALL):
            words = [word.strip() for word in match.group(1).split('،')]
            self.stop_words.extend(words)

    def get_response(self, user_message):
        cleaned_message = self.remove_stop_words(user_message)
        self.last_matched_pattern = None  # ریست کردن متغیر

        for pattern in self.patterns:
            user_pattern, bot_responses = pattern['user_pattern'], pattern['bot_responses']
            regex_pattern = self.create_regex(user_pattern)
            match = re.match(regex_pattern, cleaned_message)
            if match:
                self.last_matched_pattern = pattern  # ذخیره الگو
                response = random.choice(bot_responses)
                if response.endswith('!>'):
                    response = self.get_additional_responses(response[:-2].strip(), cleaned_message)
                return self.resolve_response(response, match.groups())

        message_words = cleaned_message.split()
        for keyword_pattern in self.keywords:
            keywords, bot_responses = keyword_pattern['keywords'], keyword_pattern['bot_responses']
            if self.contains_keywords(message_words, keywords):
                self.last_matched_pattern = keyword_pattern  # ذخیره الگو
                response = random.choice(bot_responses)
                if response.endswith('!>'):
                    response = self.get_additional_responses(response[:-2].strip(), cleaned_message)
                return self.resolve_response(response, [])
        
        return "متاسفم، متوجه نشدم."

    def remove_stop_words(self, message):
        words = message.split()
        filtered_words = [word for word in words if word not in self.stop_words]
        return ' '.join(filtered_words)

    def create_regex(self, pattern):
        return r'^' + re.sub(r'\*([0-9]*)', r'(.*?)', pattern) + r'$'

    def resolve_response(self, response, matches):
        resolved_response = response
        for i, match in enumerate(matches, start=1):
            resolved_response = resolved_response.replace(f"*{i}", match.strip())
        return re.sub(r"#(\S+)", lambda m: self.definitions.get(m.group(1), m.group(0)), resolved_response)

    def contains_keywords(self, message_words, keywords):
        return all(keyword in message_words for keyword in keywords)

    def get_additional_responses(self, initial_response, user_message):
        additional_responses = initial_response
        for pattern in self.patterns:
            user_pattern, bot_responses = pattern['user_pattern'], pattern['bot_responses']
            regex_pattern = self.create_regex(user_pattern)
            match = re.match(regex_pattern, user_message)
            if match:
                response = random.choice(bot_responses)
                additional_responses += " " + self.resolve_response(response, match.groups())
        return additional_responses

    def discover_collections(self, input_data):
        outside_text = ''
        parenthis_depth = 0
        open_parenthis = False

        for char in input_data:
            if char == '(':
                open_parenthis = True
                parenthis_depth += 1
            elif char == ')':
                parenthis_depth -= 1
                if parenthis_depth == 0:
                    open_parenthis = False
                    continue
            if not open_parenthis:
                outside_text += char

        lines = outside_text.strip().split('\n')
        for line in lines:
            if '{' in line:
                start_index = line.index('{')
                end_index = line.index('}')
                collection_name = line[:start_index].strip()
                items = [item.strip() for item in line[start_index + 1:end_index].split('،')]
                self.collections[collection_name] = items

    def check_for_collections_pattern(self, message_text):
        chunks = message_text.strip().split()
        result_text = []
        for chunk in chunks:
            is_in_collections = next((key for key, vals in self.collections.items() if chunk in vals), None)
            if is_in_collections:
                result_text.append(f'&{is_in_collections}')
            else:
                result_text.append(chunk)
        return ' '.join(result_text)