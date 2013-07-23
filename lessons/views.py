from django.shortcuts import render
from django.http import HttpResponse, Http404

from lessons.models import Lesson, Example, Question, LessonFollowsFromLesson
from user_profiles.models import UserTakesLesson

from lessons.generate import generateQuestion
from random import random

def index(request):
    latest_lesson_list = Lesson.objects.all()[:5]
    context = ({
        'latest_lesson_list':latest_lesson_list,
    })
    return render(request, 'lessons/index.html', context)

def read(request, lesson_id):
    try:
        lesson = Lesson.objects.get(pk = lesson_id)
        example_list = Example.objects.filter(lesson__id = lesson_id)
        first_question = Question.objects.filter(lesson__id = lesson_id)[0]
        next_lessons = LessonFollowsFromLesson.objects.filter(leads_from__name = lesson.name).order_by('-strength')
        context = ({'lesson': lesson,'example_list':example_list,'first_question':first_question,'next_lessons':next_lessons,})
    except Lesson.DoesNotExist:
        raise Http404
    return render(request, 'lessons/read.html', context)

def question(request, lesson_id, question_id):
    try:
        question = Question.objects.get(pk = question_id)
        pair = generateQuestion(random(), question.question, question.calculation)
        question.question = pair[0]
        question.answer = pair[1]
        context = ({'question': question,})
    except Question.DoesNotExist:
        raise Http404
    return render(request, 'lessons/question.html', context)

def skill_tree(request):
    if request.user.is_authenticated():
        curuser = request.user
        skill_tree = Lesson.objects.filter(usertakeslesson__user = curuser) #Gets all lessons that have been taken by the user
        #TODO make the above line have each lesson appear only once, also make the skill tree a tree...
    context = ({
        'skill_tree':skill_tree,
    })
    return render(request, 'lessons/skilltree.html', context)
