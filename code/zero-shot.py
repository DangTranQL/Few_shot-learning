import os
import openai 
import json
import pandas as pd
import time
import argparse
from embedding import get_embeddings, get_most_similar

parser = argparse.ArgumentParser()
# if an argument is passed in as True, we do it
parser.add_argument("--Codex")
parser.add_argument("--Explain")
parser.add_argument("--GPT3")
parser.add_argument("--GPT3_CoT")
parser.add_argument("--Do_MATH")
parser.add_argument("--Do_Courses")
args = parser.parse_args()

column_labels = ['Question', 'Original Question', 'Actual Solution']
if args.Codex == 'True':
    column_labels += ['Codex Input', 'Codex Output', 'Zero-Shot Evaluation']
if args.Explain == 'True' and args.Codex == 'True':
    column_labels += ['Codex Explanation Input', 'Codex Explanation']
if args.GPT3 == 'True':
    column_labels += ['GPT-3 Output', 'GPT-3 Evaluation']
if args.GPT3_CoT == 'True':
    column_labels += ['GPT-3 CoT Input', 'GPT-3 CoT Output', 'GPT-3 CoT Evaluation']
column_labels += ['Most Similar Questions']

openai.api_key = "YOUR KEY"
openai.Model.list()

questions_per_course = 22

codex_engine = "code-davinci-002"
gpt3_engine = "text-davinci-002"
engine_temperature = 0
engine_topP = 0
zero_shot_max_tokens = 256 
explanation_max_tokens = 150
gpt3_max_tokens = 200
gpt3_CoT_max_tokens = 1000
codex_time_delay = 3
gpt3_time_delay = 1

#locations of embeddings and which indexes refer to which questions
courses_embeddings_location = 'code/embed_data.json'
courses_embeddings_indexes = {'hw2':[0, 21]}

# for prompt formatting:
docstring_front = '''"""\n''' 
docstring_back = '''\n"""\n'''
context_array = ['write a program', 'using sympy', 'using simulations']
prompt_prefix = 'that answers the following question:'
explanation_suffix = "\n\n'''\nHere's what the above code is doing:\n1."
CoT = "Let's think step by step."

def execute_zero_shot(questions_per, 
                      embeddings_location, embeddings_indexes):
    """
    Runs zero-shot on questions_per questions for each course in courses. 
    An individual CSV file of the results is made for each course in courses.
    The embeddings for all of the questions for all of the courses in courses are located in embeddings_location.
    """
    all_embeddings = get_embeddings(embeddings_location)
    course_embeddings = all_embeddings[embeddings_indexes['hw2'][0]:embeddings_indexes['hw2'][1]+1]
    questions = []
    answers = []
    for num in range(1, questions_per + 1):
        if num < 10:
            q_num = '0' + str(num)
        else:
            q_num = str(num)
        json_location = 'C:/Users/ADMIN/Desktop/mathQ/data/hw2/hw2_Question_' + q_num + '.json'
        with open(json_location, 'r') as f:
            data = json.load(f)
        raw_question = data['Question']
        answer_to_question = data['Solution']
        questions.append(raw_question)
        answers.append(answer_to_question)

    rows = []
    for i in range(questions_per):
        question = i + 1
        original_question = questions[i]
        question_answer = answers[i]
        row = [question, original_question, question_answer]
        print('Running Zero-Shot on ' + 'hw2' + ' question ' + str(i+1) + '...')
        start = time.time()

        if args.Codex == 'True':
            time.sleep(codex_time_delay) #to avoid an openai.error.RateLimitError
            codex_input = docstring_front + context_array[0] + ' ' + prompt_prefix + ' ' + questions[i] + docstring_back
            codex_output = openai.Completion.create(engine = codex_engine, 
                                                    prompt = codex_input, 
                                                    max_tokens = zero_shot_max_tokens, 
                                                    temperature = engine_temperature, 
                                                    top_p = engine_topP)['choices'][0]['text']
            row += [codex_input, codex_output, '']

        if args.Explain == 'True' and args.Codex == 'True':
            time.sleep(codex_time_delay) #to avoid an openai.error.RateLimitError
            explanation_input = codex_input + codex_output + explanation_suffix
            explanation_output = openai.Completion.create(engine = codex_engine, 
                                                        prompt = explanation_input, 
                                                        max_tokens = explanation_max_tokens, 
                                                        temperature = engine_temperature, 
                                                        top_p = engine_topP)['choices'][0]['text']
            row += [explanation_input, explanation_output]

        if args.GPT3 == 'True':
            time.sleep(gpt3_time_delay) #to avoid an openai.error.RateLimitError
            gpt3_output = openai.Completion.create(engine = gpt3_engine, 
                                                prompt = original_question, 
                                                max_tokens = gpt3_max_tokens, 
                                                temperature = engine_temperature, 
                                                top_p = engine_topP)['choices'][0]['text']
            row += [gpt3_output, '']

        if args.GPT3_CoT == 'True':
            time.sleep(gpt3_time_delay) #to avoid an openai.error.RateLimitError
            gpt3_CoT_input = 'Q: ' + original_question + "\nA: " + CoT
            gpt3_CoT_output = openai.Completion.create(engine = gpt3_engine,
                                                prompt = gpt3_CoT_input,
                                                max_tokens = gpt3_CoT_max_tokens,
                                                temperature = engine_temperature,
                                                top_p = engine_topP)['choices'][0]['text']
            row += [gpt3_CoT_input, gpt3_CoT_output, '']

        most_similar_questions = get_most_similar(course_embeddings,i)
        row += [most_similar_questions]
        end = time.time()
        print('API call time: ' + str(end-start) + '\n')
        rows.append(row)
    info = pd.DataFrame(rows, columns=column_labels)
    course_results_location = 'C:/Users/ADMIN/Desktop/mathQ/code/csv/hw2_result.csv'
    info.to_csv(course_results_location, index=False)

if __name__ == "__main__":
    #zero-shot step for courses:

    execute_zero_shot(questions_per_course, 
                    courses_embeddings_location, courses_embeddings_indexes)
