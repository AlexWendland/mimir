from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from lessons.models import Lesson, Example, Question, LessonFollowsFromLesson
from user_profiles.models import UserTakesLesson, UserAnswersQuestion

from lessons.generate import generateQuestion
from random import random
import datetime
import re

'''
Notes:
next_link may seem completely pointless atm, and in truth it is, but when we get good (not completely random) question order sorted it will be used.
'''

def index(request):
    latest_lesson_list = Lesson.objects.all()
    context = ({
        'latest_lesson_list':latest_lesson_list,
    })
    return render(request, 'lessons/index.html', context)

def read(request, lesson_name):
    lesson = get_object_or_404(Lesson, name__iexact = lesson_name.replace("_", " "))
    next_lessons = LessonFollowsFromLesson.objects.filter(leads_from__name = lesson.name).order_by('-strength')
    questions_exist = Question.objects.filter(lesson = lesson).exists()
    context = ({'lesson': lesson,'next_lessons':next_lessons,'questions_exist':questions_exist,})
    if request.user.is_authenticated():
        if not UserTakesLesson.objects.filter(user = request.user).filter(lesson = lesson).filter(date__gt = datetime.datetime.now() - datetime.timedelta(hours=1)).exists():
            user_takes = UserTakesLesson(user=request.user,lesson=lesson)
            user_takes.save()
    return render(request, 'lessons/read.html', context)

def rate_lesson(request, lesson_id): #TODO change this so lesson_id is passed via post maybe?
    if request.user.is_authenticated():
        p = request.POST
        if "rating" in p or "comment" in p:
            user_takes_lesson = list(UserTakesLesson.objects.filter(lesson__id = lesson_id, user = request.user).order_by('-date')[:1])
            if user_takes_lesson:
                if "rating" in p:
                    user_takes_lesson[0].rating = int(p["rating"]) #TODO make this properly handle non-integer ratings so that people can't break the site by submitting funny POST requests to it.
                if "comment" in p:
                    user_takes_lesson[0].comment = p["comment"] #TODO implement this in the template and as above make sure no nasties can be placed in comments
                user_takes_lesson[0].save()
    return HttpResponse('')

def check_answer(request):
    p = request.POST
    if "question_id" in p and "answer" in p and "rand_seed" in p:
        question = get_object_or_404(Question, pk = int(p["question_id"])) #TODO make sure this makes sense, this should never go wrong in practice but who knows, possibly expand to return something more meaningful to ajax?
        if not re.match(question.answer_format.regex, p["answer"]):
            return HttpResponse('{"correct":false, "message":"Answer was not in the correct format, please correct this and try again."}', mimetype="application/json") #TODO make this message contain specifics about the format
        #TODO if user is logged in add a useranswersquestion here
        pair = generateQuestion(p["rand_seed"], question.question, question.calculation)
        if int(p["answer"]) == int(pair[1]): #TODO make this work properly with formatting so non integer answers will work.
            if request.user.is_authenticated():
                user_answers = UserAnswersQuestion(question = question, user = request.user, question_seed = p["rand_seed"], correct = True, answer = pair[1])
                user_answers.save()
            return HttpResponse('{"correct":true}', mimetype="application/json")
        else:
            #TODO mistake analysis system, no biggie
            message = "Oops, looks like you made a mistake."
            #TODO something like this: message = analyse_mistake(question, rand_seed, answer)
            if request.user.is_authenticated():
                user_answers = UserAnswersQuestion(question = question, user = request.user, question_seed = p["rand_seed"], correct = False, answer = pair[1])
                user_answers.save()
            return HttpResponse('{"correct":false, "message":"' + message + '"}', mimetype="application/json")
    return HttpResponse('')


def question(request, lesson_name, question_id):
    question = get_object_or_404(Question, pk = question_id)
    rand_seed = random()
    pair = generateQuestion(rand_seed, question.question, question.calculation)
    question.question = pair[0]
    question.answer = pair[1]
    return render(request, 'lessons/question.html', {'question': question,'next_link': reverse('lessons:rand_question', args=[lesson_name]),'rand_seed':rand_seed,})

def rand_question(request, lesson_name):
    lesson = get_object_or_404(Lesson, name__iexact = lesson_name.replace("_", " "))
    question_l = list(Question.objects.filter(lesson = lesson).order_by('?')[:1])
    if question_l:
        question = question_l[0]
        rand_seed = random()
        pair = generateQuestion(rand_seed, question.question, question.calculation)
        question.question = pair[0]
        question.answer = pair[1]
        return render(request, 'lessons/question.html', {'question': question,'next_link': reverse('lessons:rand_question', args=[lesson_name]),'rand_seed':rand_seed,})
    return HttpResponseRedirect(reverse('lessons:read', args=[lesson_name]))

def skill_tree(request):
    if request.user.is_authenticated():
        curuser = request.user
    lessons = Lesson.objects.all()
    links = LessonFollowsFromLesson.objects.all()
    context = ({
        'skill_tree':lessons, 'links':links,
    })
    return render(request, 'lessons/skilltree.html', context)
