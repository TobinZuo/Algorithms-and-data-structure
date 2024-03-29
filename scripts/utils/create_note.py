#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import time

from utils.crawl_tornado import crawl_question_info_tornado, crawl_slugs
import utils.table as table
import utils.constant as constant
from utils.create_catalog import create_catalog_tornado
from utils.common import get_detail_data
import threading
import asyncio

def create_note_content(dir, slug, lang: str):

    [[id, link, title, content, difficulty, acRate, similarQuestions, topics, file_name]] = crawl_question_info_tornado(dir, [slug])
    dir = constant.dir_dic[dir]

    solving_idea = "### 解题思路"
    complexit_analysis = "### 复杂度分析\n**时间复杂度**：$O()$。\n\n**空间复杂度**：$O()$。"
    code = "### 解题代码\n```\n```"
    # 构造笔记内容路径
    path = os.path.join(constant.codes_dir, dir, lang, file_name)
    # print(lang, path)
    # 这里检查路径是否存在是不区分大小的，但是打开文件需要，注意输入Python，而不是python
    if os.path.exists(path):
        print("code has been existed, open it.  path = {}".format(path))
        return path
    content = '\n\n'.join([solving_idea, complexit_analysis, code])
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

# =======================================================================================================
threadLock = threading.Lock()
link_content_data_multi, similar_questions_multi, related_topics_multi, file_name_multi = [], [], [], []
class create_note_frame_thread(threading.Thread):
    def __init__(self, threadID, dir, all_question_data):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.dir = dir
        self.all_question_data = all_question_data
    def run(self):
        # 新的线程必须设置新的事件循环
        asyncio.set_event_loop(asyncio.new_event_loop())
        start_time = time.time()
        print ("开始线程：", self.name)
        link_content_data, similar_questions, related_topics, file_name = \
            create_note_frame(self.dir, self.all_question_data)
        threadLock.acquire()
        link_content_data_multi.extend(link_content_data)
        similar_questions_multi.extend(similar_questions)
        related_topics_multi.extend(related_topics)
        file_name_multi.extend(file_name)
        threadLock.release()
        end_time = time.time()
        print ("退出线程：", self.name, "用时：", end_time-start_time)
# 题目信息，相似题目，相关topic
def create_note_frame(dir, all_question_data):
    link_content_data_multi, similar_questions_multi, related_topics_multi, file_name_multi = [], [], [], []
    for i, question_data in enumerate(all_question_data):
        id, link, title, content, difficulty, ac_rate, similar_questions_indexes, topics, file_name = get_detail_data(question_data)

        # 题目信息
        head = "[Toc]\n## 题目信息\n**题目链接**: {}\n".format(link)
        link_content_data = head + content

        # 相似题目
        similar_questions = "## 相似题目"
        if len(similar_questions_indexes) == 0:
            similar_questions += "\n无"
        else:
            # col_names = ['title | titleSlug | difficulty | translatedTitle']
            col_name = constant.col_name
            sim_catalog = create_catalog_tornado(dir, [], similar_questions_indexes)
            similar_questions_table = table.gen_table(col_name, sim_catalog)
            similar_questions = '\n'.join([similar_questions, similar_questions_table])

        # 相关topic
        related_topics = "## 相关topic"
        if len(topics) == 0:
            related_topics = '\n'.join([related_topics, "无"])
        else:
            # name, slug
            col_name = ["Topic", "Link"]
            topic_catalog = []
            for topic in topics:
                topic_slug = topic["slug"]
                topic_link = link[:len(link) - len(link.split("/")[-1])] + topic_slug
                topic_catalog.append([topic["name"], topic_link])
            topics_table = table.gen_table(col_name, topic_catalog)
            related_topics = '\n'.join([related_topics, topics_table])

        link_content_data_multi.append(link_content_data)
        similar_questions_multi.append(similar_questions)
        related_topics_multi.append(related_topics)
        file_name_multi.append(file_name)

    return link_content_data_multi, similar_questions_multi, related_topics_multi, file_name_multi
# =======================================================================================================

def get_note_content(dir, file_name):
    note_content = []
    for lang in os.listdir(os.path.join(constant.codes_dir, dir)):
        if file_name in os.listdir(os.path.join(constant.codes_dir, dir, lang)):
            code_path = os.path.join(constant.codes_dir, dir, lang, file_name)
            with open(code_path, encoding="utf-8") as f:
                code_data = f.read()
                note_content.append("\n".join(["## {}".format(lang), code_data]))
    return "\n".join(note_content)

def create_note(dir, slugs):
    global link_content_data_multi
    global similar_questions_multi
    global related_topics_multi
    global file_name_multi
    all_question_data = crawl_question_info_tornado(dir, slugs)
    thread_num = 3
    # 线程太多，会限制请求次数，返回429状态码
    k = len(all_question_data)//thread_num
    if k != 0:
        threads = []
        for i in range(len(all_question_data)//k):
            if i == len(all_question_data)/k:
                # print(dir, i, slugs[i*k:])
                threads.append(create_note_frame_thread(i, dir, all_question_data[i*k:]))
            else:
                # print(dir, i, slugs[i*k: i*k+k])
                threads.append(create_note_frame_thread(i, dir, all_question_data[i*k: i*k+k]))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    else:
        link_content_data_multi, similar_questions_multi, related_topics_multi, file_name_multi = create_note_frame(dir, all_question_data)
    #dir = constant.dir_dic[dir]
    for link_content_data, similar_questions, related_topics, file_name in zip(link_content_data_multi, similar_questions_multi, related_topics_multi, file_name_multi):
        note_content = get_note_content(dir, file_name)
        # 构造笔记文件路径
        path = os.path.join(constant.notes_dir, dir, file_name)
        #print(path)
        if os.path.exists(path):
            pass
            # print("note has been existed, update it！path = {}".format(path))
        else:
            print("note isn't existed, create it！path = {}".format(path))
        all_data = "\n".join([link_content_data, note_content, similar_questions, related_topics])
        #print(all_data)
        with open(path, 'w', encoding="utf-8") as f:
            f.write(all_data)
    link_content_data_multi, similar_questions_multi, related_topics_multi, file_name_multi = [], [], [], []


def create_notes():
    for dir in constant.dir_dic.values():
        titles = set()
        dir_path = os.path.join(constant.codes_dir, dir)
        for lang in os.listdir(dir_path):
            for file_name in os.listdir(os.path.join(dir_path, lang)):
                title = file_name.split(".")[-2]
                titles.add(title)
                # print(title)
        slugs = crawl_slugs(dir, list(titles))
        # print(slugs)
        create_note(dir, slugs)

