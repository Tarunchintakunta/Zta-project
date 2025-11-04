import os
import json
import re
from fuzzywuzzy import fuzz
import concurrent.futures
import spacy
from spacy.symbols import ORTH
from spacy.tokens import Doc, Span
from spacy.training import offsets_to_biluo_tags
import glob
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import time
import logging
from core.send_email import send_email
from services.create_training_data import write_training_data
from dotenv import load_dotenv
from db.db_client import DynamoDBClient
from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
from services.pdf_processing import extract_text_from_pdf
from googleapiclient.http import MediaIoBaseDownload
import io
from decimal import Decimal
import threading
from utils.utils import clean_text
import unidecode
import uuid
import traceback
import pandas as pd
import argparse


script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

progress_file = os.path.join(script_dir, "app", "data", "progress.json")
training_data_file = os.path.join(script_dir, "app", "data", "training_data_prod.json")
subjects_file = os.path.join(script_dir, "app", "data", "subjects.json")
transcript_files = os.path.join(script_dir, "app", "data","transcripts")
folder_path = os.path.join(script_dir, "app", "data", "transcript_texts") 
label_dir = os.path.join(script_dir, "app", "data", "labels_file")
TEMP_DIR = os.path.join(script_dir, "app", "data", "labeling_temp") 
city_file_path = os.path.join(script_dir, "app", "data", "constant_data", "city.json")

os.makedirs(label_dir, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

last_evaluated_key = None

file_lock=threading.Lock()
spacy.prefer_gpu()
load_dotenv()


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Convert Decimal to float
        return super().default(obj)
    
def preprocess_text(text):
    text= unidecode.unidecode(text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text

def load_all_training_data():
    training_data_files = glob.glob(training_data_file)
    all_training_data = []

    for file in training_data_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():  # Check if the file is not just whitespace
                    try:
                        data = json.loads(content)
                        for i in range(len(data)):
                            if isinstance(data[i], list) and len(data[i]) >= 2:
                                text = data[i][0]
                                annotations = data[i][1]
                                all_training_data.append((text, annotations))
                            else:
                                print(f"Skipping invalid entry at index {i} in {file}")
                    except json.JSONDecodeError as json_err:
                        print(f"Error decoding JSON in file {file}: {json_err}")
                        traceback.print_exc()
                else:
                    print(f"File is empty: {file}")
        except FileNotFoundError as fnf_error:
            print(f"File not found: {file} - {fnf_error}")
            traceback.print_exc()
            
        except Exception as e:
            print(f"Error loading file {file}: {e}")
            traceback.print_exc()
    
    return all_training_data

def generate_course_variations(course_name):
    """
    Generates a list of variations for the course name:
    - Normalized with spaces (standard form).
    - No spaces, hyphens removed.
    - Roman numerals converted to numerals (if any).
    """
    variations = set()
    
    if isinstance(course_name, list):
        for course in course_name:
            variations.update(generate_course_variations(course))  # Recurse for each item in the list
        return variations

    variations.add(course_name.lower())

    # Remove hyphens
    last_4_chars = course_name[-4:]
    course_no_hyphens = course_name.replace("-", "")
    variations.add(course_no_hyphens.lower())

    course_name_and = course_name.replace("&", "and")
    variations.add(course_name_and.lower())

    roman_to_numeral = {'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5', 'VI': '6', 'VII': '7', 'VIII': '8'}
    for roman, numeral in roman_to_numeral.items():
        numeral_course_names = re.sub(r'\b' + roman + r'\b', numeral, course_name, flags=re.IGNORECASE)
        variations.add(numeral_course_names.lower())
        
        if roman in last_4_chars:
                course_name_no_space_hyphen = " ".join(numeral_course_names.split()[:-1]) + numeral_course_names.split()[-1].replace(" ", "")
                variations.add(course_name_no_space_hyphen.lower())
                variations.add(course_name_no_space_hyphen.lower().replace("-", ""))

    numeral_to_roman = {'1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V', '6': 'VI', '7': 'VII', '8': 'VIII'}
    for numeral, roman in numeral_to_roman.items():
        roman_course_names = re.sub(r'\b' + roman + r'\b', numeral, course_name, flags=re.IGNORECASE)
        variations.add(roman_course_names.lower())
        
        if roman in last_4_chars:
            course_name_no_space_hyphen = " ".join(roman_course_names.split()[:-1]) + roman_course_names.split()[-1].replace(" ", "")
            variations.add(course_name_no_space_hyphen.lower())
            variations.add(course_name_no_space_hyphen.lower().replace("-", ""))

    
    roman_to_numeral_sorted = {k: v for k, v in sorted(roman_to_numeral.items(), key=lambda item: len(item[0]), reverse=True)}
    numeral_to_roman_sorted = {k: v for k, v in sorted(numeral_to_roman.items(), key=lambda item: int(item[0]), reverse=True)}

    for roman, numeral in roman_to_numeral_sorted.items():
        if roman.lower() in last_4_chars.lower():
            modified_last_4_chars = last_4_chars.replace(roman, numeral)
            modified_course_name = course_name[:-4] + modified_last_4_chars
            last_4 = modified_course_name[-4:]
            variations.add(modified_course_name.lower())

            if last_4.endswith(numeral) or last_4.endswith(roman):
                if last_4.endswith(numeral):
                    index = modified_course_name.upper().rfind(numeral)
                else:
                    index = modified_course_name.upper().rfind(roman)

                if index > 0:
                    if modified_course_name[index-1] != " ":
                        spaced = modified_course_name[:index] + " " + modified_course_name[index:]
                        variations.add(spaced.lower())
                        break
                    else:
                        break  

        if last_4_chars.endswith(roman) or last_4_chars.endswith(numeral):
            if last_4_chars.endswith(numeral):
                index = course_name.upper().rfind(numeral)
            else:
                index = course_name.upper().rfind(roman)

            if index > 0:
                if course_name[index-1] != " ":
                    spaced = course_name[:index] + " " + course_name[index:]
                    variations.add(spaced.lower())
                else:
                    course_name_no_space = course_name[:index - 1] + course_name[index:]
                    variations.add(course_name_no_space.lower())

    for numeral, roman in numeral_to_roman_sorted.items():
        if numeral in last_4_chars:
            modified_last_4_chars = last_4_chars.replace(numeral, roman)
            modified_course_name = course_name[:-4] + modified_last_4_chars
            last_4 = modified_course_name[-4:]
            variations.add(modified_course_name.lower())

            if last_4.endswith(numeral) or last_4.endswith(roman):
                if last_4.endswith(numeral):
                    index = modified_course_name.upper().rfind(numeral)
                else:
                    index = modified_course_name.upper().rfind(roman)

                if index > 0:
                    if modified_course_name[index-1] != " ":
                        spaced = modified_course_name[:index] + " " + modified_course_name[index:]
                        variations.add(spaced.lower())
                    else:
                        break

        if last_4_chars.endswith(roman) or last_4_chars.endswith(numeral):
            if last_4_chars.endswith(numeral):
                index = course_name.upper().rfind(numeral)
            else:
                index = course_name.upper().rfind(roman)

            if index > 0:
                if course_name[index-1] != " ":
                    spaced = course_name[:index] + " " + course_name[index:]
                    variations.add(spaced.lower())
                    break
                else:
                    course_name_no_space = course_name[:index - 1] + course_name[index:]
                    variations.add(course_name_no_space.lower())
                    break

    return list(variations)

def contains_in_before_index(page_text, start_idx):
    substring = page_text[max(0, start_idx - 4):start_idx].lower()  
    #if "in" in substring or "of" in substring or "an" in substring:
    if re.search(r'\b(in|of|an|&)\b', substring)or '&' in substring:
        return True
    return False

def discard_courses(course,start_idx,page_text):
    discard_words = ['of', 'in', 'and', '&']
    course_words = course.lower().split()
    if len(course_words) > 0 and course_words[0] in discard_words:
        return True
    start_check_idx = max(0, start_idx - 4)
    course_start = page_text[start_check_idx:start_idx].lower() 

    for word in discard_words:
        if word in course_start:
            return True

    return False

from nltk.corpus import stopwords
stop_words = set(stopwords.words('english'))
stop_words.update({'and'})

def trim_leading_stopwords(text):
    words = text.split()
    while words and words[0].lower() in stop_words:
        if words[0].lower() == 'the':
            break
        words.pop(0)
    return ' '.join(words)

roman_to_numeral = {
    'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5', 'VI': '6', 'VII': '7', 'VIII': '8',
    'IX': '9', 'X': '10', 'XI': '11', 'XII': '12', 'XIII': '13', 'XIV': '14', 'XV': '15',
    'XVI': '16', 'XVII': '17', 'XVIII': '18', 'XIX': '19', 'XX': '20'
}
def roman_to_numeral_converter(roman):
    numeral_numerals = {v: k for k, v in roman_to_numeral.items()}
    s = str(roman).upper()
    if s in roman_to_numeral:
        return roman_to_numeral[s]         # Roman → Number
    elif s in numeral_numerals:
        return numeral_numerals[s]            # Number → Roman
    else:
        return s     
# Function to check if a string is a Roman numeral
def is_roman(word):
    roman_numerals = set('IVXLCDM')
    return all(char in roman_numerals for char in word.upper())

# Function to check if a string is a regular number
def is_numeral(word):
    try:
        int(word)  # Try to convert it to integer
        return True
    except ValueError:
        return False

def get_sliding_windows(words, window_size):
    return [words[i:i+window_size] for i in range(len(words) - window_size + 1)]


def trim_to_json_bounds(text, first_word, last_word):
    words = text.split()
    try:
        start = next(i for i, w in enumerate(words) if w.lower() == first_word.lower())
    except StopIteration:
        start = 0

    try:
        end = len(words) - next(i for i, w in enumerate(reversed(words)) if w.lower() == last_word.lower())
    except StopIteration:
        end = len(words)

    return ' '.join(words[start:end])


def fuzzy_json_match(json_text, extraction_text, label,threshold=70):
    if not extraction_text.strip():
        return []

    json_words = json_text.split()
    extraction_words = extraction_text.split()
    

    window_size_25 = int(len(json_words) * 0.25)   # 25% of JSON words length (smaller)
    window_size_75 = int(len(json_words) * 0.75)   # 75% of JSON words length (slightly smaller)       # 100% of JSON words length (original size)
    window_size_100 = int(len(json_words))
    window_size_125 = int(len(json_words) * 1.25)
    window_size_150 = int(len(json_words) * 1.5)  # 125% of JSON words length (larger)

    # Create sliding windows for each of the sizes
    windows_25 = get_sliding_windows(extraction_words, window_size_25)
    windows_75 = get_sliding_windows(extraction_words, window_size_75)
    windows_100 = get_sliding_windows(extraction_words, window_size_100)
    windows_125 = get_sliding_windows(extraction_words, window_size_125)
    windows_150 = get_sliding_windows(extraction_words, window_size_150)

    # Combine all windows
    windows = windows_25 + windows_75 +  windows_125 + windows_150

    best_match = None
    best_score = 0

    for window in windows:
        window_text = ' '.join(window)
        score = fuzz.token_sort_ratio(json_text, window_text)
        #print(score)
        if score >= threshold and score > best_score:
            best_score = score
            best_match = window_text
            
    if best_match:
        trimmed = trim_to_json_bounds(best_match, json_words[0], json_words[-1])
        start_idx = extraction_text.lower().find(trimmed.lower())
        if start_idx != -1:
            end_idx = start_idx + len(trimmed)
            return [(start_idx, end_idx, label)]

    return []

def normalize_course_name(course_name):
    """
    Normalize the course name by:
    - Replacing hyphens with spaces.
    - Removing hyphens entirely (for comparison with names like 'MathematicsII').
    - Converting everything to lowercase.
    - Replacing numerals (1, 2) with their Roman counterparts (I, II).
    """
    roman_to_numeral = {'1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V', '6': 'VI', '7': 'VII', '8': 'VIII'}
    numeral_to_roman = {'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5', 'VI': '6', 'VII': '7', 'VIII': '8'}

    for numeral, roman in roman_to_numeral.items():
        course_name = course_name.replace(str(numeral), roman)

    normalized_name_with_space = course_name.replace("-", " ").lower()
    normalized_name_without_hyphen = course_name.replace("-", "").lower()

    for roman, numeral in numeral_to_roman.items():
        normalized_name_with_space = normalized_name_with_space.replace(roman, str(numeral))
        normalized_name_without_hyphen = normalized_name_without_hyphen.replace(roman, str(numeral))

    return normalized_name_with_space, normalized_name_without_hyphen


def calculate_confidence(window, course_name):
    """Calculate the fuzzy confidence level of a match between a course name and the best match string."""
    
    normalized_window = normalize_course_name(window)
    normalized_course_name = normalize_course_name(course_name)

    similarity_score = fuzz.ratio(normalized_window, normalized_course_name) / 100
    return similarity_score




def match_courses_to_pages(course_names, university, pages, course_list):
    """
    Match courses from the course list to pages using the sliding window approach with fuzzy matching.
    Each course is checked across all pages sequentially. Checks for overlapping matches and compares confidence levels.
    """
    result = []
    total_pages = len(pages)
    current_position = 0  
    all_low_confidence_matches = []  

    seen_courses = {page_number: [] for page_number in range(1, total_pages + 1)}
    course_match_counts = {course: 0 for course in course_names}
    
    
    course_names = sorted(course_names, key=lambda x: (len(x), int(re.search(r'(\d+)', x).group()) if re.search(r'(\d+)', x) else 0),reverse=True)

    for course in course_names:
        #course=clean_text(courses)
        course_found_on_pages = []  

        # Go through each page
        for page_number in range(1, total_pages + 1):
            page_text = pages[page_number - 1] 
            page_text=preprocess_text(page_text)

            matches, current_position, low_confidence_matches = sliding_window_match(page_text, [course],course_names, current_position, page_number)

            if matches:  
                for match in matches:
                    best_match = match['Best Match']

                    if len(best_match) <= 3:
                        #print(f"Skipping course '{best_match}' (length <= 3) on page {page_number}.")
                        continue
                    start_idx=match['Start Index']
                    end_idx=match['End Index']

                    current_position = end_idx

                    overlap = False
                    for seen_course in seen_courses[page_number]:
                        seen_start_idx = seen_course['Start Index']
                        seen_end_idx = seen_course['End Index']
                        seen_confidence = seen_course['Confidence']
                        seen_length = seen_end_idx - seen_start_idx

                        # Check if the new match overlaps with the seen course
                        if (start_idx < seen_end_idx and end_idx > seen_start_idx):  
                            overlap = True

                            if match['Confidence'] > seen_confidence or \
                               (match['Confidence'] == seen_confidence and (end_idx - start_idx) > seen_length):
                                # Remove the previous lower confidence or shorter match
                                seen_courses[page_number] = [course for course in seen_courses[page_number] if course['Start Index'] != seen_start_idx]
                                seen_courses[page_number].append({
                                    'Course': match['Course'],
                                    'Start Index': match['Start Index'],
                                    'End Index': match['End Index'],
                                    'Confidence': match['Confidence']
                                })
                                result = [r for r in result if not (r['Start Index'] == seen_start_idx and r['Page_number'] == page_number)]
                                result.append({
                                    'Course': match['Course'],
                                    'Start Index': match['Start Index'],
                                    'End Index': match['End Index'],
                                    'Best Match': best_match,  
                                    'Page_number': page_number,  
                                    'Confidence': match['Confidence']
                                })

                    if not overlap:
                        seen_courses[page_number].append({
                            'Course': match['Course'],
                            'Start Index': match['Start Index'],
                            'End Index': match['End Index'],
                            'Confidence': match['Confidence']
                        })

                        result.append({
                            'Course': match['Course'],
                            'Start Index': match['Start Index'],
                             'End Index': match['End Index'],
                            'Best Match': best_match,  
                            'Page_number': page_number, 
                            'Confidence': match['Confidence']
                        })

                    course_found_on_pages.append(page_number)

            current_position = 0  # Reset current_position after processing a page
        
        all_low_confidence_matches.extend(low_confidence_matches)
    
    return result, all_low_confidence_matches
    

def sliding_window_match(page_text, course_name,course_list, current_position, page_number):
    """Search for the best match of courses in the page text using a sliding window approach."""
    result = []
    
    page_words = page_text.split()
    low_confidence_matches = [] 
    processed_courses=set()

    course_names=[clean_text(course) for course in course_name if course.strip() != ""]

    if not course_names:
        return result, current_position, low_confidence_matches
    
    course_variations = generate_course_variations(course_names)

    for course in course_variations:
        course_no_space = course.replace(" ", "") 
        if course_no_space.lower() in processed_courses:
            continue
        
        processed_courses.add(course_no_space.lower())
        lab_variations = [
            f"{course.lower()} lab", 
            f"{course.lower()} laboratory", 
            f"{course.lower()} (practical)"
]
        max_confidence = 0
        best_match = ""
        start_idx = -1  
        end_idx = -1  
        
        page_text_no_space = page_text.replace(" ", "")

        course_pattern = re.escape(course_no_space)
        exact_matches = []
        for match in re.finditer(course_pattern, page_text_no_space, re.IGNORECASE):                
            start_no_space = match.start()
            end_no_space = match.end()

            if any(variation in [c.lower() for c in course_list] for variation in lab_variations):
                end_idx = end_no_space
                best_match_end_idx = end_idx  

                next_five_chars = page_text_no_space[best_match_end_idx:best_match_end_idx + 5].lower()
                next_eleven_chars=page_text_no_space[best_match_end_idx:best_match_end_idx + 11].lower()

                if 'lab' in next_five_chars or 'practical' in next_eleven_chars:
                    continue
    
            start_idx, end_idx = map_index_to_original(page_text, page_text_no_space, start_no_space, end_no_space)

            while end_idx < len(page_text) and page_text[end_idx] != " ":
                end_idx += 1

            best_match = page_text[start_idx:end_idx]                

            exact_matches.append({
                    'Course': course_name[0],
                    'Start Index': start_idx,
                    'End Index': end_idx,
                    'Best Match': best_match,
                    'Confidence': 1.0,
                    'Page_number': page_number
                })
            
        result.extend(exact_matches)

        if not exact_matches:
            course_variation=sorted(course_variations,key=lambda x:len(x),reverse=True)
            for course in course_variation:
                max_confidence = 0
                best_match = ""
                start_idx = -1  
                end_idx = -1  
                best_matches = []  

                # Sliding window search for the best match starting from current_position
                for i in range(current_position, len(page_words) - len(course.split()) + 1):
                    window = " ".join(page_words[i:i + len(course.split())])
                    
                    confidence = calculate_confidence(window, course)
                
                    if confidence > max_confidence:
                            max_confidence = confidence
                            best_match = window
                            best_match_start_idx = i

                    elif confidence==max_confidence:
                            if confidence>=0.80:
                                if best_match:
                                    best_matches.append((best_match,best_match_start_idx))
                                best_match=window
                                best_match_start_idx = i
                                best_matches.append((best_match,i))
                                same_match=[]
                                for match,idx in best_matches:
                                    course_no_space = course.replace(" ", "")
                                    match_no_space = match.replace(" ", "")
                                    match_score = fuzz.ratio(course_no_space.lower(), match_no_space.lower())
                                    same_match.append((match, match_score,idx))

                                best_match = ""
                                best_match_score = 0

                                for match, score,idx in same_match:
                                    if score >= best_match_score:
                                        best_match = match
                                        best_match_score = score
                                        best_match_start_idx = idx


                    if max_confidence>0.90:
                        continue

                    if max_confidence == 1.0:  
                        best_match = window
                        best_match_start_idx = i
                        break

                if max_confidence >= 0.80:
                        start_idx_in_text = 0
                        for j in range(best_match_start_idx):
                            start_idx_in_text += len(page_words[j]) + 1
                        
                        if any(variation in [c.lower() for c in course_list] for variation in lab_variations):
                                start_idx = page_text.find(best_match)
                                end_idx = start_idx + len(best_match)

                                best_match_end_idx = end_idx  

                                next_five_chars = page_text[best_match_end_idx:best_match_end_idx + 5].lower()
                                next_eleven_chars=page_text[best_match_end_idx:best_match_end_idx + 11].lower()

                                if 'lab' in next_five_chars or 'practical' in next_eleven_chars or 'Laboratory' in next_eleven_chars:
                                    start_idx = page_text.find(best_match, best_match_end_idx) 
        
                                    if start_idx == -1:
                                        start_idx
                                    else:
                                        start_idx = start_idx   
                                        end_idx = start_idx + len(best_match)                                        

                        special_chars_pattern=r'[.:*+?|()\[\]{}^$\s"]'

                        course_name_no_space = re.sub(special_chars_pattern, '', course)  # Remove specific special characters
                        best_match_no_space = re.sub(special_chars_pattern, '', best_match)
        
                        if len(best_match_no_space) > len(course_name_no_space):                            
                            best_trimmed_match = trim_by_words(course, best_match)

                            start_idx = page_text.find(best_trimmed_match,start_idx_in_text)
                            end_idx = start_idx + len(best_trimmed_match)

                            if discard_courses(best_trimmed_match,start_idx,page_text):
                                    continue

                            if contains_in_before_index(page_text, start_idx):
                                    continue 

                            result.append({
                                    'Course': course_name[0],
                                    'Start Index': start_idx,
                                    'End Index': end_idx,
                                    'Best Match': best_trimmed_match,
                                    'Confidence': max_confidence,
                                    'Page_number': page_number  
                                })                            
                        else:
                            if isinstance(course_name, list):
                                course_names = ' '.join(course_name)
                            best_match_words = best_match.split()
                            course_words = course_names.split()

                            if ('+' in best_match_words[0] and '+' not in course_words[0]) or \
                                ('+' in best_match_words[-1] and '+' not in course_words[-1]) or \
                                (len(best_match_words[0]) == 1 and len(course_words[0]) > 1) or \
                                (len(best_match_words[-1]) == 1 and len(course_words[-1]) > 1):
 
                                best_trimmed_match = trim_by_words(course, best_match)

                                start_idx = page_text.find(best_trimmed_match, start_idx_in_text)
                                end_idx = start_idx + len(best_trimmed_match)
                                if discard_courses(best_match,start_idx,page_text):
                                    continue

                                # Check for 'in' or 'of' before the course name, and discard if necessary
                                if contains_in_before_index(page_text, start_idx):
                                    continue  

                                result.append({
                                        'Course': course_name[0],
                                        'Start Index': start_idx,
                                        'End Index': end_idx,
                                        'Best Match': best_trimmed_match,
                                        'Confidence': max_confidence,
                                        'Page_number': page_number  
                                    })
                                current_position = end_idx
                            else:
                                start_idx = page_text.find(best_match,start_idx_in_text)
                                end_idx = start_idx + len(best_match)

                                if discard_courses(best_match,start_idx,page_text):
                                        continue

                                if contains_in_before_index(page_text, start_idx):
                                        continue  

                                result.append({
                                        'Course': course_name[0],
                                        'Start Index': start_idx,
                                        'End Index': end_idx,
                                        'Best Match': best_match,
                                        'Confidence': max_confidence,
                                        'Page_number': page_number  
                                    })
                            current_position = end_idx
                else:
                    low_confidence_matches.append({
                        'Course': course_name[0],
                        'Best Match': best_match,
                        'Confidence': max_confidence,
                        'Start Index': start_idx,
                        'End Index': end_idx,
                        'Page_number': page_number  
                    })
                    
            if best_match:
                best_match_words = best_match.split()
                for i in range(len(page_words) - len(best_match_words) + 1):
                    if page_words[i:i + len(best_match_words)] == best_match_words:
                        best_match_position = i
                        current_position = best_match_position + len(best_match_words)
                        break
    
    return result, current_position, low_confidence_matches

def map_index_to_original(page_text, page_text_no_space, start_no_space, end_no_space):
    """
    This function maps the index from the no-space text back to the original page_text with spaces.
    """
    original_start = 0
    original_end = 0
    
    page_text_pointer = 0
    page_text_no_space_pointer = 0
    
    # Find the start index by comparing the no-space version to the original text
    while page_text_pointer < len(page_text):
        if page_text[page_text_pointer] != " ":
            if page_text_no_space_pointer == start_no_space:
                original_start = page_text_pointer
            if page_text_no_space_pointer == end_no_space:
                original_end = page_text_pointer-1
                break
            page_text_no_space_pointer += 1
        page_text_pointer += 1
    
    return original_start, original_end

def trim_by_words(course_name, best_match_text):
    """Trim extra words from the best match text to improve the match with the course name."""
    
    # Split the course name and best match text into words
    best_match_text = trim_leading_stopwords(best_match_text)
    course_words = course_name.split()
    best_match_words = best_match_text.split()
    
    if len(course_words) == 0 or len(best_match_words) == 0:
        return best_match_text
    
    if len(course_words) == 1 or len(best_match_words) == 1:
        return best_match_text
    
    if ('+' in best_match_words[0][:2] and '+' not in course_name[0][:2]) or \
   (len(best_match_words[0]) == 1 and len(course_name.split()[0]) > 1):
        best_match_words = best_match_words[1:]  # Trim the first word if it contains '+'
        #print(f"Trimmed first word due to '+', best match now: {' '.join(best_match_words)}")
    
    if '+' in best_match_words[-1][-2:] and '+' not in course_name[-1][-2:]:
        best_match_words = best_match_words[:-1]  # Trim the last word if it contains '+'
        #print(f"Trimmed last word due to '+', best match now: {' '.join(best_match_words)}")

    course_name_part1 = course_words[0]
    course_name_part2 = course_words[-1]
    best_match_part1 = best_match_words[0]
    best_match_part2 = best_match_words[-1]

    if (
    # Case 1: Both are words (neither numeral nor Roman)
        (not is_roman(course_name_part2) and not is_numeral(course_name_part2) and
        not is_roman(best_match_part2) and not is_numeral(best_match_part2))
        or
        # Case 2: Both are the same (exact match)
        (best_match_part2 == course_name_part2)
        or
        # Case 3: course_name_part2 is numeral/Roman, best_match_part2 is a word
        ((is_numeral(course_name_part2) or is_roman(course_name_part2)) and
        (not is_numeral(best_match_part2) and not is_roman(best_match_part2)))
        or
        # Case 4: course_name_part2 is a word, best_match_part2 is numeral/Roman
        ((not is_numeral(course_name_part2) and not is_roman(course_name_part2)) and
        (is_numeral(best_match_part2) or is_roman(best_match_part2)))
    ):
        pass

    elif is_numeral(best_match_part2) and is_roman(course_name_part2):
        course_name_part2 = roman_to_numeral_converter(course_name_part2)  # Convert course name part to numeral

    # Case 2: If best_match_part2 is a Roman numeral and course_name_part2 is a numeral
    elif is_roman(best_match_part2) and is_numeral(course_name_part2):
        course_name_part2 = roman_to_numeral_converter(int(course_name_part2)) # Convert course name part to Roman numeral

    # Case 3: If course_name_part2 is not Roman nor Numeral, do nothing
    
    score_part1 = fuzz.ratio(course_name_part1.lower(), best_match_part1.lower())
    score_part2 = fuzz.ratio(course_name_part2.lower(), best_match_part2.lower())

    if score_part1 == 0:
        best_match_words = best_match_words[1:]
    
    if score_part2 == 0:
        best_match_words = best_match_words[:-1]
        
    # If the confidence score for the first word is below 50, combine the first two words from the best match
    elif score_part1 < 50 and len(best_match_words) > 1:
        combined_part1 = ' '.join(best_match_words[:2])  # Combine the first two words
        score_combined_part1 = fuzz.ratio(course_name_part1.lower(), combined_part1.lower())
        
        # If the combined score is still below 50, trim the first word
        if score_combined_part1 < 50:
            best_match_words = best_match_words[1:]

    # If the confidence score for the last word is below 50, combine the last two words from the best match
    elif score_part2 < 50 and len(best_match_words) > 1:
        combined_part2 = ' '.join(best_match_words[-2:])  # Combine the last two words
        score_combined_part2 = fuzz.ratio(course_name_part2.lower(), combined_part2.lower())
        
        # If the combined score is still below 50, trim the last word
        if score_combined_part2 < 50:
            best_match_words = best_match_words[:-1]

    
    best_trimmed_match = ' '.join(best_match_words)
    
    #print(f"course_name:{course_name}, best_match_text:{best_match_text}, Final trimmed match: {best_trimmed_match}")
    return best_trimmed_match

def extract_course_details_in_gap(page_text, o_mark, native_credit, grade, m_mark, start_idx, end_idx,current_page_matches_sorted,order=None):
    next_start_idx = None
    
    for i, match in enumerate(current_page_matches_sorted):
        if match['Start Index'] == start_idx:
           
            if i + 1 < len(current_page_matches_sorted):

                next_start_idx = current_page_matches_sorted[i + 1]['Start Index']
            else:
                next_start_idx=end_idx + 20
            break

    if next_start_idx:
        gap_text = page_text[end_idx:next_start_idx]

    course_details = {}

    def check_and_extract(value, value_str, gap_text, end_idx, key):
        if not value_str or value_str.strip() == "":
            return
        if value_str == "0.0":
            value_str_without_decimal = value_str.replace('.', '')
            value_str_with_decimal = value_str
        elif '.' in value_str:
            integer_part, decimal_part = value_str.split('.', 1)
            if len(integer_part) == 2:
                value_str_without_decimal = value_str[:-2]
                value_str_with_decimal = value_str
            else:
                value_str_without_decimal = value_str.replace('.', '').rstrip('0')
                value_str_with_decimal = value_str
        else:
            value_str_without_decimal = value_str
            value_str_with_decimal = value_str

        # 👇 Added: Generate more decimal variants like 2.50, 2.500, 2.5000, etc.
        try:
            normalized_float = float(value_str)
            decimal_variants = {
                f"{normalized_float:.1f}",
                f"{normalized_float:.2f}",
                f"{normalized_float:.3f}",
                f"{normalized_float:.4f}"
            }
        except ValueError:
            decimal_variants = set()

        # Also add stripped and no-decimal forms
        decimal_variants.add(value_str_with_decimal)
        decimal_variants.add(value_str_without_decimal)
        

        # Also add values like '250' (2.5) or '300' (3.0) by padding zeros
        if value_str_without_decimal.isdigit():
            for zeros in range(1, 3):  # Add '250', '2500', '25000' for example
                decimal_variants.add(value_str_without_decimal + '0' * zeros)
        padded_variants = set()
        if value_str_without_decimal.isdigit():
            for zeros in range(1, 3):
                padded_variants.add(value_str_without_decimal + '0' * zeros)

        direct_match_pattern = r'(?<=\s)' + re.escape(value_str) + r'(?=\s|\b)'
        match = re.search(direct_match_pattern, gap_text)
        if match:
            match_str = match.group(0)
        else:
            # Decimal variants
            exact_match_pattern = r'(?<=\s)' + re.escape(str(int(float(value_str)))) + r'(?=\s|\b)'
            match = re.search(exact_match_pattern, gap_text)
            if match:
                match_str = match.group(0)
            variant_pattern = r'(?<=\s)(' + '|'.join(map(re.escape, decimal_variants)) + r')(?=\s|\b)'
            match = re.search(variant_pattern, gap_text)
            if match:
                match_str = match.group(1)
            else:
                # Padded forms like '300', '3000'
                padded_pattern = r'(?<=\s)(' + '|'.join(map(re.escape, padded_variants)) + r')(?=\s|\b)'
                match = re.search(padded_pattern, gap_text)
                if match:
                    match_str = match.group(1)

        if match:
            match_str = match.group(1) if match.lastindex else match.group(0)            
            if match_str.strip() != "":
                value_start_idx = match.start() + end_idx
                value_end_idx = match.end() + end_idx
                course_details[key] = {
                    'start_idx': value_start_idx,
                    'end_idx': value_end_idx,
                    'value': " " + match_str + " "
                }

    if native_credit is not None or o_mark is not None or m_mark:
        o_mark_str = str(o_mark)
        native_credit_str = str(native_credit)

        # If o_mark != native_credit, process them separately
        if o_mark != native_credit:
            if native_credit != '':
                check_and_extract(native_credit, native_credit_str, gap_text, end_idx, 'native_credit')
            if o_mark != '':
                check_and_extract(o_mark, o_mark_str, gap_text, end_idx, 'o_mark')
        else:            
            if order:
                if len(order) == 1:
                    first_key = order[0]
                    second_key = None
                else:
                    first_key = order[0]
                    second_key = order[1]

                if first_key == 'o_mark':
                    check_and_extract(o_mark, o_mark_str, gap_text, end_idx, 'o_mark')
                    if second_key == 'native_credit':
                        # Get end index relative to gap_text for slicing
                        first_end_idx = course_details['o_mark']['end_idx'] - end_idx if 'o_mark' in course_details else 0
                        new_gap_text = gap_text[first_end_idx:]
                        check_and_extract(native_credit, native_credit_str, new_gap_text, end_idx + first_end_idx, 'native_credit')
                elif first_key == 'native_credit':
                    check_and_extract(native_credit, native_credit_str, gap_text, end_idx, 'native_credit')
                    if second_key == 'o_mark':
                        first_end_idx = course_details['native_credit']['end_idx'] - end_idx if 'native_credit' in course_details else 0
                        new_gap_text = gap_text[first_end_idx:]
                        check_and_extract(o_mark, o_mark_str, new_gap_text, end_idx + first_end_idx, 'o_mark')
                else:
                    check_and_extract(o_mark, o_mark_str, gap_text, end_idx, 'o_mark')
                    check_and_extract(native_credit, native_credit_str, gap_text, end_idx, 'native_credit')
                    
        if m_mark != 0.0 and m_mark != '':
            m_mark_str = str(m_mark)
            check_and_extract(m_mark, m_mark_str, gap_text, end_idx, 'm_mark')

    
    if grade:
        grade_str = grade
        grade_without_plus_minus = grade.replace("+", "").replace("-", "")

        grade_pattern = r'(?<=\s)' + re.escape(grade_str) + r'(?=\s)'
        grade_pattern_no_sign = r'(?<=\s)' + re.escape(grade_without_plus_minus) + r'(?=\s)'


        # Check if the grade appears in the gap text
        if re.search(grade_pattern, gap_text):
            grade_start_idx = gap_text.find(grade_str) + end_idx
            grade_end_idx = grade_start_idx + len(grade_str)
            course_details['grade'] = {
                'start_idx': grade_start_idx,
                'end_idx': grade_end_idx,
                'value': grade_str
            }

        # If grade contains '+' or '-', add the grade without these signs as a separate entity
        if grade_without_plus_minus != grade and re.search(grade_pattern_no_sign, gap_text):
            grade_start_idx_no_sign = gap_text.find(grade_without_plus_minus) + end_idx
            grade_end_idx_no_sign = grade_start_idx_no_sign + len(grade_without_plus_minus)
            course_details['grade_without_sign'] = {
                'start_idx': grade_start_idx_no_sign,
                'end_idx': grade_end_idx_no_sign,
                'value': grade_without_plus_minus
            }

    return course_details

def is_valid_cgpa_match(page_text, match_span, cgpa_value):
    try:
        # Check if it's a clean integer (no dot, no slash, etc.)
        if isinstance(cgpa_value, str) and cgpa_value.strip().isdigit():
            int_val = int(cgpa_value)
            start_idx, end_idx, _ = match_span
            context_start = max(0, start_idx - 5)
            context_end = min(len(page_text), end_idx + 5)
            context = page_text[context_start:context_end].lower()
            return "cgpa" in context
        else:
            return True  # Accept floats, "8.5", "8/10", etc. without checking
    except ValueError:
        return True  # If conversion fails, accept by default

CREDENTIAL_ABBR_MAPPING = {
    "BSc": "Bachelor of Science",
    "BA": "Bachelor of Arts",
    "BEng": "Bachelor of Engineering",
    "b.eng.":"Bachelor of Engineering",
    "B.E.": "Bachelor of Engineering",
    "B.E":"Bachelor of Engineering",
    "MSc": "Master of Science",
    "MA": "Master of Arts",
    "MBA": "Master of Business Administration",
    "PhD": "Doctor of Philosophy",
    "MTech": "Master of Technology",
    "B.Tech": "Bachelor of Technology",
    "BCA": "Bachelor of Computer Applications",
    "MCA": "Master of Computer Applications",
    "B.com": "Bachelor of Commerce",
    "BIM":"Bachelor of Information Management",
    "B.E":"Bachelor's Degree"
}

REVERSE_CREDENTIAL_MAPPING = {v: k for k, v in CREDENTIAL_ABBR_MAPPING.items()}



def match_credential_names(page_text, credential_names):
    matches = []

    for cred in [c for c in credential_names if c and c.strip() and c not in ["-", "_", "--"]]:
        candidates = set()
        cred = cred.strip()
        candidates.add(cred)

        # If the input is an abbreviation (e.g., B.E)
        if cred in CREDENTIAL_ABBR_MAPPING:
            full_form = CREDENTIAL_ABBR_MAPPING[cred]
            candidates.add(full_form)

            # Add all abbreviations that map to this full form
            for abbr, full in CREDENTIAL_ABBR_MAPPING.items():
                if full == full_form:
                    candidates.add(abbr)

        # If the input is a full form (e.g., Bachelor of Engineering)
        elif cred in REVERSE_CREDENTIAL_MAPPING:
            abbr = REVERSE_CREDENTIAL_MAPPING[cred]
            candidates.add(abbr)

            # Add all abbreviations that map to this full form
            for abbr, full in CREDENTIAL_ABBR_MAPPING.items():
                if full == cred:
                    candidates.add(abbr)

        # Final matching step with different match_type
        # for term in candidates:
        #     if term in CREDENTIAL_ABBR_MAPPING:
        #         match_type = "exact"
        #     elif term in CREDENTIAL_ABBR_MAPPING.values():
        #         match_type = "dual"
        #     else:
        #         # Default to dual for unknowns
        #         match_type = "dual"

        #     term_matches = match_entity(page_text, term, label="credential_name", match_type=match_type)
        #     matches.extend(term_matches)
        normalized_content = page_text.lower()
        for term in candidates:
            # For exact match, add word boundaries
            if term in CREDENTIAL_ABBR_MAPPING: 
                term_lower = term.lower()
                index = normalized_content.find(term_lower)

                if index != -1:
                    start_index = index
                    end_index = index + len(term_lower)
                    matches.append((start_index, end_index,"credential_name"))
            elif term in CREDENTIAL_ABBR_MAPPING.values():
                match_type = "dual"  # Flexible match (no word boundaries)
                term_pattern = term  # For dual, no need for word boundaries
                term_matches = match_entity(page_text, term_pattern, label="credential_name", match_type=match_type)
                matches.extend(term_matches)
            else:
                term_matches = match_entity(page_text, term, label="credential_name", match_type="dual")
                matches.extend(term_matches)
                # match_type = "exact"
                # #term_pattern = r'\b' + re.escape(term) + r'\b'
                # term_pattern=term

            # elif term in CREDENTIAL_ABBR_MAPPING.values():
            #     match_type = "dual"
            #     term_pattern = term  # For dual, no need for word boundaries
            # else:
            #     # Default to dual for unknowns
            #     match_type = "dual"
            #     term_pattern = term  # For dual, no need for word boundaries

            # term_matches = match_entity(page_text, term_pattern, label="credential_name", match_type=match_type)
            # matches.extend(term_matches)
    return matches


def match_entity(page_text, entry,label,match_type="dual"):
    if not entry.strip():  
        return []
    ug_entry = set()
   
    max_confidence = 0
    best_match = ""
    start_idx = -1  
    end_idx = -1  
    current_position=0  
    cleaned_entry = clean_text(entry)
    cleaned_entry_no_space = cleaned_entry.replace(" ", "")
    page_words = page_text.split()
    page_text_no_space=page_text.replace(" ","")


    if match_type == "exact":
        for match in re.finditer(re.escape(entry), page_text):
                start_idx = match.start()
                end_idx = match.end()
                matched_text = match.group()
                ug_entry.add((start_idx, end_idx, label))
    elif match_type == "dual":
        for match in re.finditer(cleaned_entry_no_space, page_text_no_space, re.IGNORECASE):                
            start_no_space = match.start()
            end_no_space = match.end()
            start_idx, end_idx = map_index_to_original(page_text, page_text_no_space, start_no_space, end_no_space)
            ug_entry.add((start_idx,end_idx,label))


        if not ug_entry and match_type in ["fuzzy", "dual"]:
            for i in range(current_position, len(page_words) - len(cleaned_entry.split()) + 1):
                window = " ".join(page_words[i:i + len(cleaned_entry.split())])
                confidence = calculate_confidence(window, cleaned_entry)

                if confidence > max_confidence:
                    max_confidence = confidence
                    best_match = window
                if max_confidence > 0.9:
                    continue  
                if max_confidence == 1.0:
                    best_match = window
                    max_confidence = confidence
                    break 

            if max_confidence >= 0.90:
                    label_no_space = entry.replace(" ", "")
                    best_match_no_space = best_match.replace(" ", "")

                    if len(best_match_no_space) >len(label_no_space):
                        best_trimmed_match = trim_by_words(entry, best_match)
                        start_idx = page_text.find(best_trimmed_match)
                        end_idx = start_idx + len(best_trimmed_match)

                        ug_entry.add((start_idx,end_idx,label))
                    else:
                        start_idx = page_text.find(best_match)
                        end_idx = start_idx + len(best_match)
                        ug_entry.add((start_idx,end_idx,label))  
            else:
                window_size = len(cleaned_entry)
                for i in range(len(page_text) - window_size + 1):
                    window = page_text[i:i + window_size]
                    cleaned_window = clean_text(window)
                    confidence = calculate_confidence(cleaned_window, cleaned_entry)

                    if confidence > max_confidence:
                        max_confidence = confidence
                        best_match = window

                    if confidence == 1.0:
                        break   
                if max_confidence >= 0.85:
                    label_no_space = entry.replace(" ", "")
                    best_match_no_space = best_match.replace(" ", "")

                    if len(best_match_no_space) >len(label_no_space):
                        best_trimmed_match = trim_by_words(entry, best_match)
                        start_idx = page_text.find(best_trimmed_match)
                        end_idx = start_idx + len(best_trimmed_match)

                        ug_entry.add((start_idx,end_idx,label))    
                    else:
                        start_idx = page_text.find(best_match)
                        end_idx = start_idx + len(best_match)
                        ug_entry.add((start_idx,end_idx,label))       

    return list(ug_entry)

def store_courses_by_major(university,country,major_courses,script_dir):
    
    try:
        if not university or str(university).strip().lower() in ["-", "","--","_", "null", "none"]:
            university = "unknown university"

        university_path=os.path.join(script_dir,"app","data","Lookup","University")
        os.makedirs(university_path, exist_ok=True)
        university_file_path=os.path.join(university_path,f"{university}.json")
        try:
            with lock:
                if os.path.exists(university_file_path):
                    #print(f"University file for {university} already exists. Updating file...")
                    with open(university_file_path,'r',encoding='utf-8') as file:
                        university_data=json.load(file)
                else:
                    university_data={}

                major_courses_lower = {major.lower(): courses for major, courses in major_courses.items()}

                for major, courses in major_courses_lower.items():
                    existing_major = None
                    
                    for key in university_data.keys():
                        if key.lower() == major:  
                            existing_major = key
                            break

                    if existing_major:
                        existing_courses=set(university_data[major]["courses"])
                        new_courses=[course for course in courses if course not in existing_courses]
                        university_data[major]["courses"].extend(new_courses)
                    else:
                        university_data[major]={"courses":courses}
                
                with open(university_file_path,'w',encoding="utf-8") as file:
                    json.dump(university_data,file,indent=4)

        except Exception as e:
            print(f"Error while acquiring file lock or writing to {university_file_path}: {e}")
            traceback.print_exc()

    except Exception as e:
        print(f"Error while storing courses for {university}: {e}")
        traceback.print_exc()

def find_courses_with_different_native_credit_and_omarks(course_list):
    different_courses = []

    # Loop through each course
    for course in course_list:
        course_name = course.get('course', '')
        native_credit = course.get('native_credit', 'N/A')
        o_mark = course.get('o_mark', 'N/A')

        # Compare native_credit and o_mark
        if native_credit != o_mark:
            different_courses.append({
                'course': course_name,
                'native_credit': native_credit,
                'o_mark': o_mark
            })
    
    return different_courses


def find_gap_for_course(course_name, course_data, matches, page_text):
    # Extract native_credit and o_mark for the given course data
    native_credit = course_data.get('native_credit', "")
    o_mark = course_data.get('o_mark', "")
    
    # Initialize flags and storage for positions
    native_first = False
    native_pos = None
    o_mark_pos = None

    # Find the index of the course in matches
    course_match = None
    for match in matches:
        if match['Course'] == course_name:
            course_match = match
            break

    if not course_match:
        return None  

    # Get the end index of the current course
    course_end_idx = course_match['End Index']

    # Find the next course's start index
    next_course_match = None
    for match in matches:
        if match['Start Index'] > course_end_idx:
            next_course_match = match
            break

    if not next_course_match:
        return None  # No next course found after this one

    # Get the start index of the next course
    next_course_start_idx = next_course_match['Start Index']

    # Extract the gap text between current course's end index and next course's start index
    gap_text = get_gap_text(course_end_idx, next_course_start_idx, page_text)

    # Check if native_credit and o_mark are present in the gap text
    native_credit_pos = find_possible_positions(native_credit, gap_text)
    o_mark_pos = find_possible_positions(o_mark, gap_text)

    result = {}

    if native_credit_pos != -1:
        result['native_credit_pos'] = native_credit_pos  # Found native_credit
    if o_mark_pos != -1:
        result['o_mark_pos'] = o_mark_pos  # Found o_mark

    if not result:
        return None  # Neither native_credit nor o_mark found in the gap

    return result



def find_possible_positions(value, gap_text):
    """Try to find numeric value in various formats, including OCR-deformed ones like 3.0 → 30."""
    if value in (None, 'N/A'):
        return -1

    try:
        val_float = float(value)
    except (ValueError, TypeError):
        return -1

    formats_to_try = {
        str(value),                     
        f"{val_float:.0f}",             
        f"{val_float:.1f}",             
        f"{val_float:.2f}",             
        str(value).replace('.', '')     
    }

    for fmt in formats_to_try:
        # Try regex with word boundary
        pattern = r'\b' + re.escape(fmt) + r'\b'
        match = re.search(pattern, gap_text)
        if match:
            return match.start()

        idx = gap_text.find(fmt)
        if idx != -1:
            return idx

    return -1

def get_gap_text(course_end_idx, next_course_start_idx, page_text):
    gap_text = ""
    for page_num, text in enumerate(page_text):
        if course_end_idx < len(text) and next_course_start_idx > 0:
            gap_text = text[course_end_idx:next_course_start_idx]
            gap_text = gap_text[:20]
            break
    return gap_text

def create_training_data(page_text, course_info,major_courses, first_name, last_name, university, major,
                         city, state, college, country, admission_year, graduation_year,credential_name,us_equivalency,program_duration,total_cgpa,
                         degrees_with_majors_and_courses):
    training_data = []
    university_matches = []
    college_matches = []
    all_university_matches = set()
    all_college_matches = set()
  
    for degree_info in degrees_with_majors_and_courses:
        university = degree_info.get("university")
        college = degree_info.get("college")        
        major_courses = {}
        major_list = degree_info.get("major")
        courses = degree_info.get("courses")

        if university and university not in ["-", "_", "--"]:
            university_matches =  match_entity(page_text, university, "university", match_type="dual")
            if university_matches:
                all_university_matches.update(university_matches)
                training_data.extend(all_university_matches)
            else:
                university_matches = fuzzy_json_match(university, page_text, label="university", threshold=70)
                if university_matches:
                    training_data.extend(university_matches)

        if college and college not in ["-", "_", "--"]:
            college_matches =  match_entity(page_text, college, "college", match_type="dual")
            if college_matches:
                all_college_matches.update(college_matches)
                training_data.extend(all_college_matches)
            else:
                college_matches = fuzzy_json_match(college, page_text, label="college", threshold=70)
                if college_matches:
                    training_data.extend(college_matches)

        if major_list and courses:
            major_courses[major_list] = courses
        else:
            continue 

        if all_university_matches and all_college_matches:
            for uni_match in all_university_matches:
                uni_start_idx = uni_match[0]  
            for col_match in all_college_matches:
                col_start_idx = col_match[0]
            if uni_start_idx < col_start_idx: 
                filename = university
                store_courses_by_major(filename, country, major_courses, script_dir)
            else: 
                filename = college
                store_courses_by_major(filename, country, major_courses, script_dir)

        elif all_university_matches:
            filename = university
            store_courses_by_major(university,country,major_courses,script_dir)
        elif all_college_matches:
            store_courses_by_major(college,country,major_courses,script_dir)
        else:
            store_courses_by_major(university,country,major_courses,script_dir)
            store_courses_by_major(college,country,major_courses,script_dir)  

    if major and major not in ["-", "_", "--"]:
        for major in [i for i in major if i!=None]:
            major_matches = match_entity(page_text, major, "major", match_type="dual")
            if major_matches:
                training_data.extend(major_matches)
 
    if city and city not in ["-", "_", "--"]:
        for city in [i for i in city if i!=None]:
            city_matches = match_entity(page_text, city, "city", match_type="dual")
            if city_matches:
                training_data.extend(city_matches)

    if state and state not in ["-", "_", "--"]:
        for state in [i for i in state if i!=None]:
            if state in city:  
                continue
            state_matches = match_entity(page_text, state, "state", match_type="dual")
            if state_matches:
                training_data.extend(state_matches)

    if first_name and first_name not in ["-", "_", "--"]:
        first_name_matches = match_entity(page_text, first_name, "first_name", match_type="dual")
        if first_name_matches:
            training_data.extend(first_name_matches)

    if last_name and last_name not in ["-", "_", "--"]:
        if len(last_name.strip()) == 1:
            if first_name_matches:
                for match in first_name_matches:
                    first_name_end = match[1]
                    context_after = page_text[first_name_end:first_name_end + 3]
                    if not context_after.startswith(last_name):
                        index_after = context_after.find(last_name)
                        if index_after != -1:
                            abs_index_after = first_name_end + index_after
                            training_data.append((abs_index_after, abs_index_after + 1, "last_name"))

                    first_name_start = match[0]
                    context_before_start = max(0, first_name_start - 3)
                    context_before = page_text[context_before_start:first_name_start]
                    if not context_before.endswith(last_name):
                        index_before = context_before.rfind(last_name)
                        if index_before != -1:
                            abs_index_before = context_before_start + index_before
                            training_data.append((abs_index_before, abs_index_before + 1, "last_name"))
        else:
            # For multi-char last names
            last_name_matches = match_entity(page_text, last_name, "last_name", match_type="dual")
            if last_name_matches:
                training_data.extend(last_name_matches)
 
    if country and country not in ["-", "_", "--"]:
        for country in [i for i in country if i!=None]:
            country_matches = match_entity(page_text, country, "country", match_type="dual")
            if country_matches:
                training_data.extend(country_matches)
                    
    for year in range(1900, 2026):
        year_str = str(year)
        year_matches = match_entity(page_text, year_str, "year", match_type="exact")
        if year_matches:
            training_data.extend(year_matches)


    # Create reverse mapping (full → abbr)
    if credential_name and credential_name not in ["-", "_", "--"]:
        credential_name_matches = match_credential_names(page_text, credential_name)
        training_data.extend(credential_name_matches)

    if course_info:
        training_data.extend(course_info)

    if total_cgpa and total_cgpa not in ["-", "_", "--"]:
        if isinstance(total_cgpa, list):
            for cgpa in total_cgpa:
                if isinstance(cgpa, str):  
                    if "//" in cgpa:
                        parts = cgpa.split("//")
                        if len(parts) == 2:
                            before_slash, after_slash = parts
                            if before_slash.strip() and after_slash.strip():
                                total_cgpa_matches = match_entity(page_text, before_slash, "total_cgpa", match_type="exact")
                                total_cgpa_match = match_entity(page_text, cgpa, "total_cgpa", match_type="exact")
                                if total_cgpa_matches:
                                    training_data.extend(total_cgpa_matches)
                                if total_cgpa_match:
                                    training_data.extend(total_cgpa_match)
                            else:
                                continue
                        else:
                            continue

                    elif "/" in cgpa:
                        parts = cgpa.split("/")
                        if len(parts) == 2:
                            before_slash, after_slash = parts
                            if before_slash.strip() and after_slash.strip():
                                total_cgpa_matches = match_entity(page_text, before_slash, "total_cgpa", match_type="exact")
                                total_cgpa_match = match_entity(page_text, cgpa, "total_cgpa", match_type="exact")
                                if total_cgpa_matches:
                                    training_data.extend(total_cgpa_matches)
                                if total_cgpa_match:
                                    training_data.extend(total_cgpa_match)
                            else:
                                continue
                        else:
                            continue

                    else:
                        total_cgpa_matches = match_entity(page_text,cgpa, "total_cgpa", match_type="exact")
                        if total_cgpa_matches:
                            for match in total_cgpa_matches:
                                if is_valid_cgpa_match(page_text, match, cgpa):
                                    training_data.append(match)
 
    return (page_text, {"entities": training_data})

def checkStructuredAndUnstructuredData(text):
    text = text.split()
    count = 0
    if len(text)<3:
        return True
    if len(text)>50:
        return False
    for i in range(min(6, len(text))):  
        if len(text[i]) <= 2:
            count += 1
            if count == 5:
                return True
    return False


def find_semester_matches(page_text):
    """Find and match semesters including Roman and Arabic numerals in the page text, and return matches with page number."""
    
    
    semester_pattern = r'\b(?:first|second|third|fourth|fifth|sixth|seventh|eighth|[1-8]|I|II|III|IV|V|VI|VII|VIII)\s?(?:semester|sem)|(?:semester|sem)\s?(?:first|second|third|fourth|fifth|sixth|seventh|eighth|[1-8]|I|II|III|IV|V|VI|VII|VIII)\b|' \
                  r'(?:semester|sem)\s?(?:first|second|third|fourth|fifth|sixth|seventh|eighth|[1-8]|I|II|III|IV|V|VI|VII|VIII)\s?(?:year)\s?(?:first|second|third|fourth|fifth|sixth|seventh|eighth|[1-8]|I|II|III|IV|V|VI|VII|VIII)\b|' \
                  r'(?:spring|fall)\s?(?:2014|2015|2016|2017|2018|2019|2020|2021|2022|2023|2024)\b'


    matches = []
    for match in re.finditer(semester_pattern, page_text, re.IGNORECASE):  # Case insensitive match
        if match: 
            start_idx = match.start()
            end_idx = match.end()
            matched_text = match.group(0)

            if len(matched_text) <= 2:
                continue  
            matches.append((start_idx, end_idx, matched_text))

    combined_matches = []
    i = 0
    while i < len(matches):
        if len(matches[i]) < 3:  
            i += 1
            continue

        current_match = matches[i]
        start_idx, end_idx, matched_text = current_match
        
        if i + 1 < len(matches):
            next_match = matches[i + 1]
            
            if len(next_match) < 3:  
                i += 1
                continue

            next_start_idx, next_end_idx, next_matched_text = next_match            

            if ("semester" in matched_text.lower() and "year" in next_matched_text.lower()):
                combined_text = matched_text + " " + next_matched_text
                combined_matches.append((start_idx, next_end_idx, combined_text))  
                i += 2  
                continue

        combined_matches.append((start_idx, end_idx, matched_text))  
        i += 1

    return combined_matches
 

def process_pdf_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

            app_id = data.get("appid", "")
            dynamo_data = data.get("dynamoDb", {})
            page_text = data.get("page_text", "")  
            all_training_data = []
            matches = []
            combined_info = {
                "app_id": app_id,
                "sk": dynamo_data.get("sk", ""),
                "pk": dynamo_data.get("pk", ""),
                "first_name": dynamo_data.get("first_name", ""),
                "last_name": dynamo_data.get("last_name", ""),
                "universities": set(),
                "college":set(),
                "countries": set(),
                "cities": set(),
                "states": set(),
                "majors": set(),
                "credential_names": set(),
                "total_cgpas": [],
                "gpa_letter_grades": [],
                "admission_year": [],
                "graduation_years": [],
                "is_degree_awarded": [],
                "program_durations": [],
                "us_equivalencies": set(),
                "total_m_marks": [],
                "total_o_mark": [],
                "scales": set(),
                "courses": [],
                "degrees_with_majors_and_courses": []
            }

            for key, degree in dynamo_data.items():
                if key.startswith("degree") and isinstance(degree, dict):
                    combined_info["universities"].add(degree.get("university"))
                    combined_info["college"].add(degree.get("college"))
                    combined_info["countries"].add(degree.get("country"))
                    combined_info["cities"].add(degree.get("city"))
                    combined_info["states"].add(degree.get("state"))
                    combined_info["majors"].add(degree.get("major"))
                    combined_info["credential_names"].add(degree.get("credential_name"))
                    combined_info["total_cgpas"].append(degree.get("total_cgpa"))
                    combined_info["gpa_letter_grades"].append(degree.get("gpa_letter_grade"))
                    combined_info["admission_year"].append(degree.get("admission_year"))
                    combined_info["graduation_years"].append(degree.get("graduation_year"))
                    combined_info["is_degree_awarded"].append(degree.get("is_degree_awarded", False))
                    combined_info["program_durations"].append(degree.get("program_duration"))
                    combined_info["us_equivalencies"].add(degree.get("us_equivalency"))
                    combined_info["total_m_marks"].append(degree.get("total_m_marks"))
                    combined_info["total_o_mark"].append(degree.get("total_o_mark"))
                    combined_info["scales"].add(degree.get("scale"))
                    combined_info["degrees_with_majors_and_courses"].append({
                        "degree_key": key,
                        "university": degree.get("university"),
                        "college":degree.get("college"),
                        "major": degree.get("major"),
                        "courses": [c.get("course") for c in degree.get("course", []) if c.get("course")]})

                    for course in degree.get("course", []):
                        combined_info["courses"].append(course)
                    
            
            for key in combined_info:
                if isinstance(combined_info[key], set):
                    combined_info[key] = [value for value in combined_info[key] if value]

            if page_text and degree:
                course_list=combined_info.get("courses")
            different_courses = find_courses_with_different_native_credit_and_omarks(course_list)

            if different_courses:                
                course_names = [course['course'] for course in course_list]
                sorted_page_numbers = sorted(page_text.keys(), key=lambda x: int(re.search(r'\d+', x).group()))
                page_content= [page_text[page_num] for page_num in sorted_page_numbers]
                pages=[preprocess_text(page) for page in page_content ]

                university =combined_info.get("universities") or None
                first_name = combined_info.get("first_name") or None
                last_name = combined_info.get("last_name") or None
                major = combined_info.get("majors") or None
                city = combined_info.get("cities") or None
                state = combined_info.get("states") or None
                college =combined_info.get("college") or None
                country = combined_info.get("countries") or None
                admission_year =combined_info.get("admission_year") or None
                graduation_year = combined_info.get("graduation_years") or None
                credential_name =combined_info.get("credential_names") or None
                program_duration =combined_info.get("program_durations") or None
                total_cgpa =combined_info.get("total_cgpas") or None
                us_equivalency = combined_info.get("us_equivalencies") or None

                major_courses = {}

                if isinstance(major, list):
                    majors = ", ".join(major)  
                else:
                    majors = str(major) if major else "Unknown Major"
                courses = [course['course'] for course in course_list]
                
                major_courses[majors] = courses

                matches, low_confidence_matches = match_courses_to_pages(course_names, university, pages, course_list)
                check_count = 0
                order = ['native_credit', 'o_mark'] 
                for course in different_courses:
                    course_name = course['course']
                    native_credit = course['native_credit']
                    o_mark = course['o_mark']

                    result = find_gap_for_course(course_name, course, matches,pages)

                    if result:
                        # Get the positions of native_credit_pos and o_mark_pos from the result
                        native_credit_pos = result.get('native_credit_pos')
                        o_mark_pos = result.get('o_mark_pos')

                        if native_credit_pos is not None and o_mark_pos is not None:
                            if native_credit_pos < o_mark_pos:
                                # Store the static labels in the correct order
                                order = ['native_credit', 'o_mark']  # native_credit comes first
                            else:
                                order = ['o_mark', 'native_credit'] 
                            check_count += 1 # o_mark comes first
                        elif native_credit_pos is not None:
                            order = ['native_credit']
                            check_count += 1  # Only native_credit is available
                        elif o_mark_pos is not None:
                            order = ['o_mark']
                            check_count += 1 
                        break 

                sem_info = []
                sem_matches = []
            
                for page_idx, page in enumerate(pages):
                    sem_match = find_semester_matches(page)
                    for match in sem_match:
                        start_idx, end_idx, _ = match
                        sem_matches.append((start_idx, end_idx, "semester", page_idx + 1))  # Page index + 1 for 1-based index

                    # Add the found semester matches to the sem_info
                if sem_matches:
                    sem_info.extend(sem_matches)

                for page_idx, page in enumerate(pages):
                    if not page.strip():  
                        continue  

                    if checkStructuredAndUnstructuredData(page):
                        continue  

                    course_info = []
                    seen_course_labels = set()
                    seen_o_mark_labels = set()
                    seen_native_credit_labels = set()
                    seen_grade_labels = set()
                    seen_m_mark_labels = set()

                    for match in matches[:]: 
                        if match['Page_number'] == page_idx + 1:  
                            course_name = match['Course']

                            start_idx = match['Start Index']
                            end_idx = match['End Index']
                            best_match = match['Best Match']

                            course_detail = [course for course in course_list if course['course'] == course_name]

                            if course_detail:
                                for course_details in course_detail:
                                    o_mark = course_details.get('o_mark', "")
                                    native_credit = course_details.get('native_credit', "")
                                    grade = course_details.get('grade',"")
                                    m_mark = course_details.get('m_mark',"")
                                
                                    current_page_matches = [m for m in matches if m['Page_number'] == page_idx + 1]
                                    current_page_matches_sorted = sorted(current_page_matches, key=lambda x: x['Start Index'])

                                    course_detail_info = extract_course_details_in_gap(page, o_mark, native_credit, grade, m_mark, start_idx, end_idx,current_page_matches_sorted,order)

                                    if (start_idx, end_idx) not in seen_course_labels:
                                        course_info.append([start_idx, end_idx, "course"])
                                        seen_course_labels.add((start_idx, end_idx)) 

                                    if 'o_mark' in course_detail_info and (course_detail_info['o_mark']['start_idx'], course_detail_info['o_mark']['end_idx']) not in seen_o_mark_labels:
                                        course_info.append([course_detail_info['o_mark']['start_idx'], course_detail_info['o_mark']['end_idx'], "o_mark"])
                                        seen_o_mark_labels.add((course_detail_info['o_mark']['start_idx'], course_detail_info['o_mark']['end_idx']))  # Mark as seen

                                    if 'native_credit' in course_detail_info and (course_detail_info['native_credit']['start_idx'], course_detail_info['native_credit']['end_idx']) not in seen_native_credit_labels:
                                        course_info.append([course_detail_info['native_credit']['start_idx'], course_detail_info['native_credit']['end_idx'], "native_credit"])
                                        seen_native_credit_labels.add((course_detail_info['native_credit']['start_idx'], course_detail_info['native_credit']['end_idx']))  # Mark as seen
                        
                                    if 'grade' in course_detail_info and (course_detail_info['grade']['start_idx'], course_detail_info['grade']['end_idx']) not in seen_grade_labels:
                                        course_info.append([course_detail_info['grade']['start_idx'], course_detail_info['grade']['end_idx'], "grade"])
                                        seen_grade_labels.add((course_detail_info['grade']['start_idx'], course_detail_info['grade']['end_idx']))  # Mark as seen

                                    if 'm_mark' in course_detail_info and (course_detail_info['m_mark']['start_idx'], course_detail_info['m_mark']['end_idx']) not in seen_m_mark_labels:
                                        course_info.append([course_detail_info['m_mark']['start_idx'], course_detail_info['m_mark']['end_idx'], "m_mark"])
                                        seen_m_mark_labels.add((course_detail_info['m_mark']['start_idx'], course_detail_info['m_mark']['end_idx']))  # Mark as seen
                           
                            matches.remove(match)

                    # Add semester-related entities to course_info
                    for sem_match in sem_info:
                        start_idx = sem_match[0]
                        end_idx = sem_match[1]
                        semester = sem_match[2]
                        page_num = sem_match[3]

                        # Process the semester match if it's on the current page and not processed yet
                        if page_num == page_idx + 1:
                            if (start_idx, end_idx) not in seen_course_labels:  
                                sem_matches = ((start_idx, end_idx, "semester"))
                                course_info.append(sem_matches)
                                seen_course_labels.add((start_idx, end_idx)) 
                        
                    all_entities_sorted = sorted(course_info, key=lambda x: x[0])
                    

                    course_info = [label for label in course_info if label[0] != label[1]]
                    course_info = [label for label in course_info if label[0] != -1]

                    training_data = create_training_data(page.upper(), all_entities_sorted,major_courses, first_name, last_name, university, major,
                                                         city, state, college, country, admission_year, graduation_year,
                                                         credential_name, us_equivalency, program_duration,total_cgpa,
                                                         degrees_with_majors_and_courses=combined_info["degrees_with_majors_and_courses"]
                                                         )

                    all_training_data.append(training_data)

    except FileNotFoundError as fnf_error:
        print(f"File not found: {file_path} - {fnf_error}")
        traceback.print_exc()
    except json.JSONDecodeError as json_err:
        print(f"Error decoding JSON file {file_path}: {json_err}")
        traceback.print_exc()
    except Exception as e:
        print(f"Error processing entry {data.get('appid', 'unknown')} in file {file_path}: {e}")
        traceback.print_exc()

    return all_training_data


def create_supplementary_data(input_file, output_file, label="entity"):
    with open(input_file, "r") as file:
        course_titles = json.load(file)

    course_titles = list(set(course_titles))
    course_titles_upper = [i.strip().upper() for i in course_titles if i.isascii() and len(i.strip()) >= 4 and len(i.strip()) <= 150]


    courses = course_titles_upper  

    # Format courses for NER
    formatted_courses = [
        [
            course,
            {
                "entities": [
                    [0, len(course), label]
                ]
            }
        ]
        for course in courses
    ]

    if os.path.exists(output_file):
        with open(output_file, "r") as outfile:
            existing_data = json.load(outfile)
    else:
        existing_data = []
    existing_data.extend(formatted_courses)

    # Write formatted data to output file
    with open(output_file, "w") as outfile:
        json.dump(existing_data, outfile, indent=4)

    #print(f"Formatted courses have been written to {output_file}")


def correctData(start,end,text):
    if len(text[start:end]) != len(text[start:end].strip()):
        leftSpaces = len(text[start:end]) - len(text[start:end].lstrip())
        rightSpaces = len(text[start:end]) - len(text[start:end].rstrip())
        start =start + leftSpaces
        end =end - rightSpaces
    while(start > 0 and start < len(text) and text[start-1] != ' '):                
        start = start - 1
    while(end < len(text) and end > 0 and text[end] != ' ' ):
        end = end + 1
    if start <= end :
        return (start,end)
    else:
        return (-1,-1)


def add_data_to_file(filename, data):
    try:
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            with open(filename, 'r') as file:
                existing_data = json.load(file)  
            existing_data.extend(data)  

            with open(filename, 'w') as file:
                json.dump(existing_data, file, indent=2)  
        else:
            with open(filename, 'w') as file:
                json.dump(data, file, indent=2)  

        #print(f"Data successfully added to {filename}.")
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()



def add_entity_text(input_string, entity_data):
        updated_entities = []
        for entity_info in entity_data:
            start_index, end_index, entity_type = entity_info
            entity_text = input_string[start_index:end_index]
            updated_entities.append((start_index,end_index,entity_type,entity_text))
        return updated_entities


def save_skipped_entities_to_file(skipped_entities, problematicEntries,reason_count):
    try:
        skipped_data = []

        for entry in skipped_entities:
            text = entry["text"] 
            if isinstance(entry["entity"], tuple) and len(entry["entity"]) == 3:
                start, end, label = entry["entity"]
                entity_value = text[start:end] 
                #skipped_data.append([text, {"entities": [(start, end, label, entity_value)]}])
                skipped_data.append([text, {"entities": [(start, end, label)]}])

        problematicEntries.extend(skipped_data)

        try:
            with open("training_data_prod_errors.json", 'r') as file:
                existing_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []

        # Append the new problematic entries to the existing data
        existing_data.extend(problematicEntries)

        with open("training_data_prod_errors.json", 'w') as file:
            json.dump(existing_data, file, indent=2)


    except Exception as e:
        print(f"An error occurred while saving problematic entities: {e}")
        traceback.print_exc()


def convert_entities_to_tuples(entities, text, skipped_entities,reason_count):
    PRIORITY_LIST = [
        "university",  "first_name", "last_name", "credential_name",
        "major", "college","course","country", "city", "state","native_credit",
        "o_mark", "m_mark", "grade", "year", "semester", "total_cgpa"
    ]
    LABEL_PRIORITY = {label: len(PRIORITY_LIST) - idx for idx, label in enumerate(PRIORITY_LIST)}

    flattened_entities = []
    spans_set = set()
    group_entry = []

    entities_sorted = sorted(entities, key=lambda x: x[0])
    for entity in entities_sorted:
        if isinstance(entity, (tuple, list)) and len(entity) == 3:
            start, end, label = entity

            if text[start:end] == " ":
                start+=1
                end+=1
                reason = "empty spaces (-1)"
                reason_count[reason] = reason_count.get(reason, 0) + 1
                continue
                #print("handled -1")
            
            entity_text = text[start:end]
            if label == "course" and len(entity_text) <= 3:
                reason = "Courses length less than 3 "
                reason_count[reason] = reason_count.get(reason, 0) + 1
                #print(f"Skipping 'course' entity with length less than or equal to 3: {(start, end, label)}")
                continue
                        


            if start >= len(text):
                reason = "Invalid start index"
                reason_count[reason] = reason_count.get(reason, 0) + 1
                #print(f"Skipping entity with invalid start index: {(start, end, label)}")
                #skipped_entities.append({"reason": "Invalid start index", "entity": (start, end, label), "text": text})
                continue

            if start is None or end is None:
                reason = "Start or End is None"
                reason_count[reason] = reason_count.get(reason, 0) + 1
                #print(f"Skipping invalid entity due to None values: {(start, end, label)}")
                #skipped_entities.append({"reason": "Start or End is None", "entity": (start, end, label), "text": text})
                continue

            # Correct the start and end positions
            (start, end) = correctData(start, end, text)

            if start == -1 or end == -1:  # Skip invalid entities after correction
                reason = "Invalid start or end after correction"
                reason_count[reason] = reason_count.get(reason, 0) + 1
                #print(f"Skipping invalid entity after correction: {(start, end, label)}")
                #skipped_entities.append({"reason": "Invalid start or end after correction", "entity": (start, end, label), "text": text})
                continue



            entity_inside_another = False
            entity_inside_another = False
            for i, (existing_start, existing_end, existing_label) in enumerate(group_entry):
                if start < existing_end and end > existing_start:
                    current_priority = LABEL_PRIORITY.get(label, 0)
                    existing_priority = LABEL_PRIORITY.get(existing_label, 0)
                    
                    if start == existing_start and end == existing_end:
                        if current_priority > existing_priority:
                            group_entry.remove((existing_start, existing_end, existing_label))
                            group_entry.append((start, end, label))
                            reason = f"Replaced {existing_label} with {label} due to higher priority (same span)"
                            reason_count[reason] = reason_count.get(reason, 0) + 1
                        else:
                            reason = f"Skipped {label} because {existing_label} has higher or equal priority (same span)"
                            reason_count[reason] = reason_count.get(reason, 0) + 1
                            skipped_entities.append({
                                "reason": reason,
                                "entity": (start, end, label),
                                "text": text
                            })
                        entity_inside_another = True
                        break

                    if start >= existing_start and end <= existing_end:
                        # New entity is inside the existing entity, so skip it
                        entity_inside_another = True
                        reason = f"Skipping {label} because it is inside {existing_label}"
                        reason_count[reason] = reason_count.get(reason, 0) + 1
                        skipped_entities.append({"reason": reason, "entity": (start, end, label), "text": text})
                        break

                    # Case 2: Existing entity is completely inside the new entity
                    elif existing_start >= start and existing_end <= end:
                        # Existing entity is inside the new one, so remove it
                        entity_inside_another = True
                        # Remove the existing entity from group_entry
                        group_entry = [(es, ee, el) for es, ee, el in group_entry if (es, ee) != (existing_start, existing_end)]
                        reason = f"Removed {existing_label} because it is inside {label}"
                        reason_count[reason] = reason_count.get(reason, 0) + 1
                        group_entry.append((start, end, label))
                        break

                    if current_priority > existing_priority:
                        group_entry.remove((existing_start, existing_end, existing_label))
                        group_entry.append((start, end, label))
                        reason = f"{label} priority over {existing_label}"
                        reason_count[reason] = reason_count.get(reason, 0) + 1
                        break
                    elif current_priority < existing_priority:
                        reason = f"{existing_label} priority over {label}"
                        reason_count[reason] = reason_count.get(reason, 0) + 1
                        skipped_entities.append({
                            "reason": reason,
                            "entity": (start, end, label),
                            "text": text
                        })
                        entity_inside_another = True
                        break
                    else:
                        if (end - start) > (existing_end - existing_start):
                            group_entry.remove((existing_start, existing_end, existing_label))
                            group_entry.append((start, end, label))
                            reason = "Overlapping entity replaced due to equal priority and greater length"
                            reason_count[reason] = reason_count.get(reason, 0) + 1
                            break
                        else:
                            reason = "Overlapping entity with equal priority and shorter or equal length"
                            reason_count[reason] = reason_count.get(reason, 0) + 1
                            skipped_entities.append({
                                "reason": reason,
                                "entity": (start, end, label),
                                "text": text
                            })
                            entity_inside_another = True
                            break            

            if entity_inside_another:
                continue


            if (start, end) not in spans_set:
                overlapping = any(start < existing_end and end > existing_start for (existing_start, existing_end, _) in group_entry)
                if not overlapping:
                    group_entry.append((start, end, label))
                    spans_set.add((start, end))
                else:
                    reason = "Overlapping entity"
                    reason_count[reason] = reason_count.get(reason, 0) + 1
                    skipped_entities.append({"reason": "Overlapping entity", "entity": (start, end, label), "text": text})
                    continue
            else:
                reason = "Duplicate entity"
                reason_count[reason] = reason_count.get(reason, 0) + 1
                continue
        else:
            reason = "Invalid entity format"
            reason_count[reason] = reason_count.get(reason, 0) + 1
            skipped_entities.append({"reason": "Invalid entity format", "entity": entity, "text": text})

    # Only add non-empty groups
    if group_entry:
        flattened_entities.append(group_entry)

    return flattened_entities

lock = threading.Lock()

def process_pdf_file_and_correct(file_path, skipped_entities):
    all_training_data = process_pdf_file(file_path)

    # === Step 1: Save raw file ===
    filename = os.path.basename(file_path)  # e.g. "Application_121766.json"
    # #base_id = filename.replace("Application_", "").replace(".json", "")+ "labeled_data"  # "121766"
    # base_id = filename.replace("App#slu", "").replace(".json", "")  # "121766"
    base_id = filename.replace("Application_", "").replace("App#slu", "").replace(".json", "")


    RAW_OUTPUT_DIR = "/home/suman/Project/ModelBasedAITransanscriptReading/app/data/raw_training_data"
    CORRECTED_OUTPUT_DIR = "/home/suman/Project/ModelBasedAITransanscriptReading/app/data/corrected_training_data"

    os.makedirs(RAW_OUTPUT_DIR, exist_ok=True)
    os.makedirs(CORRECTED_OUTPUT_DIR, exist_ok=True)

    raw_output_path = os.path.join(RAW_OUTPUT_DIR, f"{base_id}.json")
    corrected_output_path = os.path.join(CORRECTED_OUTPUT_DIR, f"{base_id}.json")

    try:
        with open(raw_output_path, "w", encoding="utf-8") as f:
            json.dump(all_training_data, f, ensure_ascii=False, indent=4)
        #print(f"✅ Saved raw training data to: {raw_output_path}")
    except Exception as e:
        print(f"Error saving raw data for {file_path}: {e}")

    # === Step 2: Continue correction as before ===
    temp_filename = f"temp_{uuid.uuid4().hex}.json"
    temp_file_path = os.path.join(TEMP_DIR, temp_filename)

    with open(temp_file_path, 'w', encoding='utf-8') as f:
        json.dump(all_training_data, f, ensure_ascii=False, indent=4)

    try:
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
    except Exception as e:
        print(f"Failed to load temp file {temp_file_path}: {e}")
        traceback.print_exc()
        return []

    nlp = spacy.blank("en")
    special_case = [{ORTH: "I"}, {ORTH: "I"}]
    nlp.tokenizer.add_special_case("II", special_case)

    correctEntries = []
    problematicEntries = []
    reason_count = {}

    for data in all_data:
        text = data[0]
        entities = convert_entities_to_tuples(data[1]['entities'], text, skipped_entities, reason_count)

        doc = nlp.make_doc(text)
        correctInaPage = []
        problemsInaPage = []

        for entry in entities:
            biluo_tags = offsets_to_biluo_tags(doc, entry)
            hasIssue = '-' in biluo_tags
            if hasIssue:
                entry = add_entity_text(text, entry)
                problemsInaPage.extend(entry)
            else:
                correctInaPage.extend(entry)

        if correctInaPage:
            correctEntries.append([text, {"entities": correctInaPage}])
        if problemsInaPage:
            problematicEntries.append([text, {"entities": problemsInaPage}])

    try:
        with open(corrected_output_path, 'w', encoding='utf-8') as f:
            json.dump(correctEntries, f, ensure_ascii=False, indent=4)
        print(f"✅ Saved corrected data to: {corrected_output_path}")
    except Exception as e:
        print(f"❌ Error saving corrected data for {file_path}: {e}")

    # Optional: overwrite temp file with corrected data (as before)
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        json.dump(correctEntries, f, ensure_ascii=False, indent=4)

    # Save skipped/problematic entities
    with lock:
        save_skipped_entities_to_file(skipped_entities, problematicEntries, reason_count)

    return correctEntries



def aggregate_temp_files_to_corrected(corrected_data_path):
    temp_files = [f for f in os.listdir(TEMP_DIR) if f.endswith(".json")]
    combined_data = []

    for temp_file in temp_files:
        temp_path = os.path.join(TEMP_DIR, temp_file)
        try:
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    combined_data.extend(data)
        except Exception as e:
            print(f"Error reading temp file {temp_path}: {e}")
            traceback.print_exc()
        finally:
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Error deleting temp file {temp_path}: {e}")
                traceback.print_exc()

    try:
        if os.path.exists(corrected_data_path):
            with open(corrected_data_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        else:
            existing = []

        existing.extend(combined_data)

        with open(corrected_data_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error writing to {corrected_data_path}: {e}")
        traceback.print_exc()


def process_files_in_parallel(folder_path):
    corrected_file_path = os.path.join(label_dir,"training_data_prod_corrected.json")
    errors_file_path = os.path.join(label_dir,"training_data_prod_errors.json")

    try:
        with open(corrected_file_path, 'w', encoding='utf-8') as corrected_file:
            json.dump([], corrected_file)
    except IOError as e:
        print(f"Error clearing {corrected_file_path}: {e}")
        traceback.print_exc()
        return

    try:
        with open(errors_file_path, 'w', encoding='utf-8') as errors_file:
            json.dump([], errors_file)
    except IOError as e:
        print(f"Error clearing {errors_file_path}: {e}")
        traceback.print_exc()
        return

    file_paths = [os.path.join(folder_path, filename) for filename in os.listdir(folder_path) if filename.endswith(".json")]

    all_matches = []
    skipped_entities = []

    total_files = len(file_paths)
    completed_files = 0
    progress_width = 50
    print("\nLabeling: |" + "-" * progress_width + f"| 0% (0/{total_files} PDFs)", end='', flush=True)
    max_workers = int(os.getenv('MAX_WORKERS', 5))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_pdf_file_and_correct, file_path, skipped_entities) for file_path in file_paths]

        for future in concurrent.futures.as_completed(futures):
            matches = future.result()
            all_matches.extend(matches)
            completed_files += 1

            # Update progress bar
            progress = completed_files / total_files
            filled_length = int(progress_width * progress)
            bar = '█' * filled_length + '-' * (progress_width - filled_length)
            percentage = int(100 * progress)
            print(f'\rLabeling: |{bar}| {percentage}% ({completed_files}/{total_files} PDFs)', end='', flush=True)

            temp_files = [f for f in os.listdir(TEMP_DIR) if f.endswith(".json")]
            if len(temp_files) >= 50 or completed_files == total_files:
                aggregate_temp_files_to_corrected(corrected_file_path)

    print()
    return all_matches



def replace_prod_with_corrected_data():
    corrected_file_path = os.path.join(label_dir,"training_data_prod_corrected.json")
    training_data_prod_path = os.path.join(script_dir, "app", "data", "training_data_prod.json")

    # Load the corrected data from the corrected JSON file
    try:
        with open(corrected_file_path, 'r', encoding='utf-8') as corrected_file:
            corrected_data = json.load(corrected_file)
    except FileNotFoundError:
        print(f"Error: The file {corrected_file_path} was not found.")
        traceback.print_exc()
        return
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {corrected_file_path}.")
        traceback.print_exc()
        return

    try:
        with open(training_data_prod_path, 'w', encoding='utf-8') as prod_file:
            # Empty the file by writing an empty list or JSON structure
            json.dump([], prod_file)  # or `prod_file.truncate(0)` to clear it
        
    except IOError as e:
        print(f"Error clearing {training_data_prod_path}: {e}")
        traceback.print_exc()
        return

    try:
        with open(training_data_prod_path, 'w', encoding='utf-8') as prod_file:
            json.dump(corrected_data, prod_file, ensure_ascii=False, indent=4)
        
    except IOError as e:
        print(f"Error writing to {training_data_prod_path}: {e}")
        traceback.print_exc()

def save_matches_to_file(matches, filename=training_data_file):
    """Save the list of matches to a JSON file."""
    output_data = []

    for match in matches:
        output_data.append(match)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)



# Set up logging configuration
logging.basicConfig(
    filename='cpu_monitor.log',  # Log file name
    level=logging.INFO,          # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

def get_pdf_files_offline(pdf_files_dir,org_code):
    pdf_filenames = [f for f in os.listdir(pdf_files_dir) if f.endswith(".pdf")]
    pdf_files_offline = []

    for filename in pdf_filenames:
        filename_no_ext = filename.rsplit(".", 1)[0]  
        parts = filename_no_ext.split("_")  
        if len(parts) == 2:  
            _, right = parts
            pdf_files_offline.append(f"App#{org_code}{right}")
        else:
            print(f"Skipping file {filename}: Unexpected filename format")  

    return pdf_files_offline

def is_cpu_idle(threshold=30):
    """
    Check if the CPU usage is below a specified threshold.
    """
    # return psutil.cpu_percent(interval=1) < threshold
    

def run_function_when_idle(func, threshold=30, check_interval=5):
    """
    Runs the given function when the CPU is idle, based on the specified threshold.
    
    Args:
        func: The function to execute.
        threshold: The CPU usage threshold below which the function should run.
        check_interval: The interval in seconds to check CPU usage.
    """
    while True:
        if True:
            logging.info("CPU is idle, running the function...")
            func()
            # Check if the last_evaluated_key is None to decide whether to break the loop
            global last_evaluated_key
            if last_evaluated_key is None:
                logging.info("No more data to process. Stopping the process.")
                break
        else:
            logging.info(f"CPU is busy. Checking again in {check_interval} seconds...")
            time.sleep(check_interval)

def execute_training_data_creation():
    """
    Check for the existence of the progress file and pass lastEvaluatedKey to write_training_data if it exists.
    """
    global last_evaluated_key  # Ensure we use the global last_evaluated_key variable

    progress_data = None
    # Check if progress file exists
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r") as file:
                progress_data = json.load(file)
                last_evaluated_key = progress_data.get("lastEvaluatedKey")
                logging.info(f"Found last_evaluatedKey: {last_evaluated_key}")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON from the progress file: {e}")
        except Exception as e:
            logging.error(f"Error reading the progress file: {e}")

    # Initial call to write_training_data to handle the first iteration when lastEvaluatedKey is None
    try:
        
        parser = argparse.ArgumentParser(description="Organization code for processing PDF files")
        parser.add_argument("--sk", type=str, help="Organisation sk", default="Organisation#Saint Louis University")
        args = parser.parse_args()
        logging.info("Executing write_training_data function for the first iteration...")
        asyncio.run(write_training_data(args.sk, last_evaluated_key))
    except Exception as e:
        logging.error(f"Error during the first execution of write_training_data: {e}")
        return

    # Send email after the first iteration
    send_email(
        "Training Data creation process update",
        f'Hi Team,\n\nFirst iteration completed. LastEvaluatedKey: {last_evaluated_key}\n\nBest regards,\nYour AI System',
        os.getenv("RECEIVER_EMAIL")
    )

    # Check if lastEvaluatedKey is None after the first execution, to decide whether to continue the loop
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r") as file:
                progress_data = json.load(file)
                last_evaluated_key = progress_data.get("lastEvaluatedKey")
                logging.info(f"Updated last_evaluatedKey: {last_evaluated_key}")
        except Exception as e:
            logging.error(f"Error reading progress file after the first execution: {e}")
            return

    # Continue processing if last_evaluated_key is not None
    while last_evaluated_key is not None:
        try:
            parser = argparse.ArgumentParser(description="Organization code for processing PDF files")
            parser.add_argument("--sk", type=str, help="Organisation sk", default="Organisation#Saint Louis University")
            args = parser.parse_args()
            logging.info("Executing write_training_data function for the first iteration...")
            asyncio.run(write_training_data(args.sk, last_evaluated_key))


            # After the execution, update the last_evaluated_key
            if os.path.exists(progress_file):
                with open(progress_file, "r") as file:
                    progress_data = json.load(file)
                    last_evaluated_key = progress_data.get("lastEvaluatedKey")
                    logging.info(f"Updated last_evaluated_key: {last_evaluated_key}")

            # If the last_evaluated_key becomes None, exit the loop
            if last_evaluated_key is None:
                logging.info("All data processed. Exiting.")
                break

            # Send email after each iteration with the updated progress log
            send_email(
                "Training Data creation progress update",
                f'Hi Team,\n\nNew iteration completed. LastEvaluatedKey: {last_evaluated_key}\n\nBest regards,\nYour AI System',
                os.getenv("RECEIVER_EMAIL")
            )

        except Exception as e:
            logging.error(f"Error while executing write_training_data: {e}")
            break

    # Send a final email notification once processing is finished
    send_email(
        "Training Data creation process finished",
        f'Hi Team,\n\nTraining Data process has finished. Previous progress data: {progress_data}\n\nBest regards,\nYour AI System',
        os.getenv("RECEIVER_EMAIL")
    )


def load_data(file_path):
    """Load data from a JSON file and return it. Defaults to an empty list if not found."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File {file_path} not found. Returning an empty list.")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding the JSON file: {file_path}. Returning an empty list.")
        return []

def write_subject_names(courses):

    subjects = load_data(subjects_file)
    unique_subjects = set(subjects)

    for item in courses:
        course_name = item.get("course")
        if course_name:
            unique_subjects.add(course_name)
    updated_subjects = sorted(unique_subjects)

    with open(subjects_file, "w") as file:
        json.dump(updated_subjects, file, indent=4)


def save_training_data(new_training_data):
    # Load existing data if the file exists
    if os.path.exists(training_data_file):
        with open(training_data_file, "r") as file:
            existing_data = json.load(file)
    else:
        existing_data = []

    existing_data.extend(new_training_data)

    with open(training_data_file, "w") as file:
        json.dump(existing_data, file, indent=2)


def get_credentials(credentials: dict, drive_tokens: dict):
    try:
        # Extract data from credentials and drive tokens
        cred_data = credentials["installed"]

        creds = Credentials(
            token=drive_tokens["access_token"],
            refresh_token=drive_tokens["refresh_token"],
            token_uri=cred_data["token_uri"],
            client_id=cred_data["client_id"],
            client_secret=cred_data["client_secret"],
            scopes=[drive_tokens["scope"]],
        )

        return creds
    except KeyError as e:
        raise HTTPException(
            status_code=500, detail=f"Missing key in the provided data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

async def download_file(service, file_name):

    try:
        file_path = os.path.join(transcript_files, file_name + '.pdf')

        if os.path.exists(file_path):
            # print(f"{file_name} already downloaded.")
            # Read the existing file into a BytesIO object for further processing
            with open(file_path, 'rb') as f:
                file_io = io.BytesIO(f.read())
            file_io.seek(0)  # Reset the pointer to the beginning
            return file_io,None

        # Query to get the file from Google Drive
        query = f"mimeType='application/pdf' and (name='{file_name}.pdf' or name='{file_name}')"

        results = (
            service.files()
            .list(q=query, pageSize=1, fields="nextPageToken, files(id, name)")
            .execute()
        )
        drive_files = results.get("files", [])

        if drive_files:
            file_id = drive_files[0]["id"]
            request = service.files().get_media(fileId=file_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                # print(f"Download {int(status.progress() * 100)}%.")

            # Save the file as a PDF to the specified folder after download
            file_io.seek(0)
            with open(file_path, 'wb') as f:
                f.write(file_io.read())

            # Return the file IO for further processing
            file_io.seek(0)
            return file_io,None

    
        return None,file_name
    except Exception as e:
        print("Error in downloading file", e)
        traceback.print_exc()


async def generate_and_save_json( app, text,file_path):
    degrees = {key: value for key, value in app.items() if key.startswith('degree')}

    combined_data = {
        "appid": app.get("sk", ""),
        "dynamoDb": app,  
        "page_text": text
    }

    try:
        with open(file_path, "w") as json_file:
            json.dump(combined_data, json_file, indent=4, cls=DecimalEncoder)
        #print(f"Data successfully saved to {file_path}")
    except Exception as e:
        print(f"Error saving JSON for Application ID {app.get('sk')}: {e}")
        traceback.print_exc()


def extract_fields(app_data, fields):

    extracted_data = {}
    for field in fields:
        extracted_data[field] = [
            degree_value.get(field)
            for degree_key, degree_value in app_data.items()
            if degree_key.startswith("degree") and degree_value.get(field)
        ]
    return extracted_data

def log_missing_app_id(app_id):
    try:
        no_data_file = os.path.join(label_dir, "noappdata.json")

        if os.path.exists(no_data_file):
            try:
                with open(no_data_file, "r") as f:
                    content = f.read().strip()
                    no_data_list = json.loads(content) if content else []
            except json.JSONDecodeError:
                print(f"[Warning] Failed to decode {no_data_file}, starting fresh.")
                no_data_list = []
        else:
            no_data_list = []

        if app_id not in no_data_list:
            no_data_list.append(app_id)

        with open(no_data_file, "w") as f:
            json.dump(no_data_list, f, indent=4)

    except Exception as e:
        print(f"[Error] Failed to log missing app ID {app_id}: {e}")

def update_json_data(label, json_file_path):
    if label:
        with file_lock:
            if os.path.exists(json_file_path):
                try:
                    with open(json_file_path, "r") as f:
                        content = f.read().strip()
                        existing_data = json.loads(content) if content else []
                except json.JSONDecodeError:
                    print(f"[Warning] Invalid JSON in {json_file_path}. Reinitializing as empty list.")
                    traceback.print_exc()
                    existing_data = []
            else:
                existing_data = []

            if isinstance(label, dict):
                if isinstance(existing_data, dict): 
                    if not any(k in existing_data for k in label.keys()):
                        existing_data.update(label)                   
                else:
                    existing_data = label
            else:
                if label not in existing_data:
                    existing_data.append(label)

            with open(json_file_path, "w") as f:
                json.dump(existing_data, f, indent=4)
    else:
        print(f"Warning: No data to update for {json_file_path}")

def update_progress_bar(json_tracker):

        #download_tracker["completed"] += 1
        completed = json_tracker["completed"]
        total = json_tracker["total"]
        percentage = int((completed / total) * 100)
        progress_width = 30
        filled_length = int(progress_width * percentage // 100)
        bar = '█' * filled_length + '-' * (progress_width - filled_length)

        print(f'\rJson Progress: |{bar}| {percentage}% ({completed}/{total} PDFs)', end='', flush=True)



async def process_application(
    orgCode,
    app,
    course_list,
    service,extracted_data,json_tracker
):
 
    try:
        file_name = "Application_" + app.get("sk", "").split(f"App#{orgCode.lower()}")[1]
 
        fields_to_update = {
            'city': 'city.json',
            'state': 'EduState.json',
            'college': 'college.json',
            'country': 'country.json',
            'major': 'Major.json',
            'grade': 'Grades.json',
            'university': 'University.json',
            'sem': 'Sem_data.json',
            'credential_name':'credential.json'
        }
 
        
        for field, json_filename in fields_to_update.items():
            field_name=extracted_data.get(field)

            if field == "credential_name":
                credential_duration_map = {}
                credential_names = extracted_data.get("credential_name", [])
                program_durations = extracted_data.get("program_duration", [])

                for name, duration in zip(credential_names, program_durations):
                    credential_duration_map[name] = int(duration)
                    update_json_data(credential_duration_map, os.path.join(script_dir,"app", "data", "constant_data",json_filename))                
            else:        
                for label in [i for i in field_name if i!=None]:
                    update_json_data(label, os.path.join(script_dir,"app", "data", "constant_data",json_filename))
    
        course_names = [course['course'] for course in course_list if len(course['course']) <= 150]
        for course in course_names:
            update_json_data(course,os.path.join(script_dir,"app", "data", "constant_data","subjects.json"))
  
        for degree_key in app:
            major_courses={}
            if degree_key.startswith("degree"):
                degree_data=app.get(degree_key)
                if degree_data:
                    university=degree_data.get('university',"unknown university")
                    major=degree_data.get('major')
                    country=degree_data.get('country')
                    courses = [course['course'] for course in degree_data.get('course', [])]
                    major_courses[major] = courses
 
                          
        file_io,msg = await download_file(service, file_name)
 
        if msg:  # If there's a message, assume it's a failure
            labeling_file = os.path.join(label_dir, "missing_drive_pdfs.json")
 
            if os.path.exists(labeling_file):
                with open(labeling_file, 'r') as f:
                    labeling_data = json.load(f)
            else:
                labeling_data = {}
 
            # Append the msg under the specified key
            labeling_data.setdefault("pdf not found in drive", []).append(msg)
 
            # Save the file
            with open(labeling_file, 'w') as f:
                json.dump(labeling_data, f, indent=4)
        if not file_io:
                return
 
 
        folder_path = os.path.join(script_dir, "app", "data", "transcript_texts")
        json_file_name = f"{app.get('sk', 'application')}.json"
        json_file_path = os.path.join(folder_path, json_file_name)
 
        if os.path.exists(json_file_path):
            # print(f"JSON file {json_file_name} already exists. Skipping JSON generation.")
            return  
 
        os.makedirs(folder_path, exist_ok=True)
 
        text_data, word_confidence_lookup,store_pattern = extract_text_from_pdf(file_io)

        if not text_data:
            print(f"Warning: No text extracted from the PDF for Application ID: {app.get('sk')}")
            return
 
        await generate_and_save_json(app, text_data,json_file_path)
        json_tracker["completed"]+=1
 
        update_progress_bar(json_tracker)     
 
 
    except Exception as e:
        print(f"Error processing application for {app.get('sk')}: {e}")
        traceback.print_exc()
 
        return []
 
 
async def write_training_data(sk,lastEvalkey,mode=os.getenv("MODE")):

    try:
        ddb_client = DynamoDBClient()
            # Query for organization data
        orgData, last_evaluated_key2 = ddb_client.query_items(
                table_name="CredEval",
                key_condition="#pk=:pk and #sk=:sk",
                projection_expression="#pk, #sk, #name, #code, #import_csv_folder_id, #drive_tokens, #drive_credentials, #import_transcripts_folder_id",
                expression_attribute_names={
                    "#pk": "pk",
                    "#sk": "sk",
                    "#name": "name",
                    "#code": "code",
                    "#import_csv_folder_id": "import_csv_folder_id",
                    "#drive_tokens": "drive_tokens",
                    "#drive_credentials": "drive_credentials",
                    "#import_transcripts_folder_id": "import_transcripts_folder_id",
                },
                #filter_expression="#code = :code or #code = :smallCaseCode or #code = :capitalCaseCode",
                expression_attribute_values={
                    ":pk": "Organisation#",
                    ":sk":sk,                    
                },
            )
 
            # Check if orgData is empty
        if not orgData:
                print("No organization data found.")
                return
        orgCode=orgData[0]["code"].lower()

    except Exception as e:
        print(f"[ERROR] Failed to fetch organization data for sk={sk}: {e}")
        traceback.print_exc()
        return
    
    PROJECTION_EXPRESSION="#pk, #sk, #first_name,#last_name,#degree1, #degree2, #degree3, #degree4, #degree5, #degree6, #degree7, #degree8, #degree9, #degree10"
    EXPRESSION_ATTRIBUTE_NAMES={
    "#pk": "pk","#sk": "sk",
    "#first_name": "first_name","#last_name": "last_name",
    "#degree1": "degree1","#degree2": "degree2","#degree3": "degree3",
    "#degree4": "degree4","#degree5": "degree5","#degree6": "degree6",
    "#degree7": "degree7","#degree8": "degree8","#degree9": "degree9",
    "#degree10": "degree10"} 

    fields_to_extract = ["city", "college","grade","state","university","sem","country", "major","credential_name","program_duration"]
                    
    if mode.lower()== "online": 
        try:
            appData, last_evaluated_key = ddb_client.query_items(
                table_name="CredEval",
                key_condition="#pk=:pk and begins_with(#sk,:sk)",
                projection_expression=PROJECTION_EXPRESSION,
                expression_attribute_names=EXPRESSION_ATTRIBUTE_NAMES,
                expression_attribute_values={":pk": "App#", ":sk": "App#"+orgCode},
                last_evaluated_key=lastEvalkey
            )
 
            if not appData:
                print(f"No application data found for org code: {orgCode}.")
                log_missing_app_id(app_id)
                

            creds = get_credentials(orgData[0]["drive_credentials"], orgData[0]["drive_tokens"])
            service = build("drive", "v3", credentials=creds)
 
            # Initialize progress log data
            progress_log_file = progress_file
            progress_log = None
            if os.path.exists(progress_log_file):
                with open(progress_log_file, "r") as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1]
                        progress_log = json.loads(last_line)
                        applications_processed = progress_log.get("applicationsProcessed", 0)
                    else:
                        applications_processed = 0
            else:
                progress_log = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "lastEvaluatedKey": None,
                    "applicationsProcessed": 0,
                }
                applications_processed = 0
            
            print(f"Creating tasks for {len(appData)} applications")
            courses=[]
            total_files = len(appData)
            download_tracker = {"completed": 0, "total": total_files}
            lock = asyncio.Lock()
             
            tasks = [
                process_application(
                    orgCode,
                    app,
                    [
                        course
                        for degree_key in app
                        if degree_key.startswith('degree')  # Ensure it processes only degree-related keys
                        for course in app.get(degree_key, {}).get("course", [])
                    ],
                    service,extract_fields(app, fields_to_extract),download_tracker
                )
                for app in appData]
            
 
            await asyncio.gather(*tasks)
            
 
            if os.path.exists(os.path.join(label_dir, "pdf_not_found.json")):
                with open(os.path.join(label_dir, "pdf_not_found.json"), 'r') as file:
                    labeling_data = json.load(file)
                not_found_list = labeling_data.get("pdf not found in drive", [])
                failed_count = len(not_found_list)
            else:
                failed_count = 0
 
            successful_count = len(tasks) - failed_count
            print(f"Processing completed for {successful_count} applications out of {len(tasks)}.")
            if os.path.exists(os.path.join(label_dir, "pdf_not_found.json")):
                with open(os.path.join(label_dir, "pdf_not_found.json"), 'r+') as file:
                    labeling_data = json.load(file)
 
                    # Get current list of pdfs not found
                    current_not_found = labeling_data.get("pdf not found in drive", [])
 
                    # Append to the "all pdfs not found in drive" key
                    if "all pdfs not found in drive" not in labeling_data:
                        labeling_data["all pdfs not found in drive"] = []
 
                    labeling_data["all pdfs not found in drive"].extend(current_not_found)
 
                    # Delete the "pdf not found in drive" key
                    if "pdf not found in drive" in labeling_data:
                        del labeling_data["pdf not found in drive"]
 
                    # Write back the updated JSON
                    file.seek(0)
                    json.dump(labeling_data, file, indent=4)
                    file.truncate()
 
 
            if progress_log:
                progress_log.update({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "lastEvaluatedKey": last_evaluated_key,
                    "applicationsProcessed": applications_processed,
                })
            else:
                progress_log = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "lastEvaluatedKey": last_evaluated_key,
                    "applicationsProcessed": applications_processed,
                }
 
            with open(progress_log_file, "w") as f:
                json.dump(progress_log, f)
                f.write("\n")
 
        except Exception as err:
            error_log = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(err),
            }
            print(f"Error creating dynamic training data: {error_log}")
            traceback.print_exc()
    

    elif mode.lower()== "offline":
        app_ids_to_check = get_pdf_files_offline(transcript_files, orgCode)
        tasks = []

        try:
            download_tracker={"completed": 0, "total": len(app_ids_to_check)}
            json_tracker = {"completed": 0, "total": len(app_ids_to_check)}

            for app_id in app_ids_to_check:
                folder_path = os.path.join(script_dir, "app", "data", "transcript_texts")
                json_file_name = f"{app_id}.json"
                json_file_path = os.path.join(folder_path, json_file_name)


                if os.path.exists(json_file_path):
                    download_tracker["completed"]+=1
                    json_tracker["completed"]+=1
                    update_progress_bar(json_tracker)
                    continue


                else:
                # Query application data
                    appData, last_evaluated_key = ddb_client.query_items(
                        table_name="CredEval",
                        key_condition="#pk=:pk and #sk=:sk",
                        projection_expression=PROJECTION_EXPRESSION,
                        expression_attribute_names=EXPRESSION_ATTRIBUTE_NAMES,
                        expression_attribute_values={
                            ":pk": "App#",
                            ":sk": app_id
                        },
                    )

                    if not appData:
                        print(f"Application {app_id} not found. Skipping...")
                        log_missing_app_id(app_id)
                        continue

                    creds = get_credentials(orgData[0]["drive_credentials"], orgData[0]["drive_tokens"])
                    service = build("drive", "v3", credentials=creds)

                    courses=[]
                    courses = [
                        course
                        for degree_key in appData[0]
                        if degree_key.startswith('degree')
                        for course in appData[0].get(degree_key, {}).get("course", [])
                    ]
                    extracted_data = extract_fields(appData[0], fields_to_extract)
                    tasks.append(process_application(orgCode, appData[0], courses, service, extracted_data,json_tracker))


            await asyncio.gather(*tasks)

        except Exception as err:
            error_log = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(err),
            }
            print(f"Error creating dynamic training data: {error_log}")
            traceback.print_exc()


    elif mode.lower()== "excel":
        try:
            excel_df = pd.read_excel(os.getenv("EXCEL_PATH"))
            tasks = []
            excel_number_map = {}
            for idx, row in excel_df.iterrows():
                sk = row.get("sk", "")
                if isinstance(sk, str):
                    excel_number_map[sk] = row
            
            app_ids_to_check = get_pdf_files_offline(transcript_files, orgCode)
            download_tracker={"completed": 0, "total": len(app_ids_to_check)}
            json_tracker = {"completed": 0, "total": len(app_ids_to_check)}

            for app_id in app_ids_to_check:
                folder_path = os.path.join(script_dir, "app", "data", "transcript_texts")
                json_file_name = f"{app_id}.json"
                json_file_path = os.path.join(folder_path, json_file_name)


                if os.path.exists(json_file_path):
                    download_tracker["completed"]+=1
                    json_tracker["completed"]+=1
                    update_progress_bar(json_tracker)
                    continue

                else:
                    if app_id in excel_number_map:
                        matched_row = excel_number_map[app_id]
                        
                        appData = {}
                        
                        for field in ["sk", "pk", "first_name", "last_name"]:
                            if pd.notna(matched_row.get(field)):
                                val = matched_row[field]
                                try:
                                    parsed = json.loads(val) if isinstance(val, str) and val.strip().startswith("{") else val
                                    appData[field] = parsed
                                
                                except Exception as e:
                                    appData[field] = val
                                    print(f"[ERROR] Failed to parse {field} for {app_id}: {e}")
                                    traceback.print_exc()

                        num_degrees = int(matched_row.get("no_of_degree", 0))  

                        for i in range(1, num_degrees + 1):
                            deg_col = f"degree{i}"
                            if pd.notna(matched_row.get(deg_col)):
                                try:
                                    degree_raw = json.loads(matched_row[deg_col])
                                    degree_clean = {}

                                    for key, val in degree_raw.items():
                                        if isinstance(val, dict) and "S" in val:
                                            degree_clean[key] = val["S"]
                                        elif isinstance(val, dict) and "N" in val:
                                            degree_clean[key] = float(val["N"])
                                        elif isinstance(val, dict) and "BOOL" in val:
                                            degree_clean[key] = val["BOOL"]
                                        elif isinstance(val, dict) and "L" in val:
                                                # List of maps (Courses)
                                            degree_clean[key] = [
                                                {k: float(v["N"]) if "N" in v else v["S"]
                                                    for k, v in item["M"].items()}
                                                    for item in val["L"]
                                                ]
                                        else:
                                            degree_clean[key] = val

                                    appData[deg_col] = degree_clean

                                except Exception as e:
                                    print(f"[ERROR] Failed to parse {deg_col} for {app_id}: {e}")
                                    traceback.print_exc()
                        courses=[]
                        courses = [
                                course
                                for degree_key in appData
                                if degree_key.startswith('degree')
                                for course in appData.get(degree_key, {}).get("course", [])
                                ]
                                        
                        extracted_data = extract_fields(appData, fields_to_extract)
                        tasks.append(process_application(orgCode, appData, courses, None, extracted_data,json_tracker))
                                                                        
            await asyncio.gather(*tasks)
        
        except Exception as e:
            print(f"[ERROR] An error occurred while processing Excel data: {e}")
            traceback.print_exc()

def post_processing_pipeline():
    try:
        all_matches = process_files_in_parallel(folder_path)
        save_matches_to_file(all_matches)
        replace_prod_with_corrected_data()
    except Exception as e:
        print(f"Error during post-processing: {e}")
        traceback.print_exc()

def main():
    execute_training_data_creation()
    post_processing_pipeline()

run_function_when_idle(main, threshold=20, check_interval=10)


current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(current_dir))

with open(os.path.join(base_dir, "app", "data", "training_data_constant.json"), "w") as outfile:
    json.dump([], outfile) 

create_supplementary_data(os.path.join(base_dir, "app", "data", "constant_data", "subjects.json"), output_file=os.path.join(base_dir, "app", "data", "training_data_constant.json"), label="course")
create_supplementary_data(os.path.join(base_dir, "app", "data", "constant_data", "city.json"), output_file=os.path.join(base_dir, "app", "data", "training_data_constant.json"), label="city")
create_supplementary_data(os.path.join(base_dir, "app", "data", "constant_data", "college.json"), output_file=os.path.join(base_dir, "app", "data", "training_data_constant.json"), label="college")
create_supplementary_data(os.path.join(base_dir, "app", "data", "constant_data", "Grades.json"), output_file=os.path.join(base_dir, "app", "data", "training_data_constant.json"), label="grade")
create_supplementary_data(os.path.join(base_dir, "app", "data", "constant_data", "EduState.json"), output_file=os.path.join(base_dir, "app", "data", "training_data_constant.json"), label="state")
create_supplementary_data(os.path.join(base_dir, "app", "data", "constant_data", "University.json"), output_file=os.path.join(base_dir, "app", "data", "training_data_constant.json"), label="university")
create_supplementary_data(os.path.join(base_dir, "app", "data", "constant_data", "Sem_data.json"), output_file=os.path.join(base_dir, "app", "data", "training_data_constant.json"), label="semester")
create_supplementary_data(os.path.join(base_dir, "app", "data", "constant_data", "country.json"), output_file=os.path.join(base_dir, "app", "data", "training_data_constant.json"), label="country")
create_supplementary_data(os.path.join(base_dir, "app", "data", "constant_data", "Major.json"), output_file=os.path.join(base_dir, "app", "data", "training_data_constant.json"), label="major")

if os.path.isdir(TEMP_DIR) and not os.listdir(TEMP_DIR):
    try:
        os.rmdir(TEMP_DIR)
    except Exception as e:
        pass
    
logging.shutdown()