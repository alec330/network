from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
import json
from django.http import JsonResponse

from .models import User, Post, Follow, Like

def remove_like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    like = Like.objects.filter(user=user, post=post)
    like.delete()
    return JsonResponse({"message": "Unliked!"})

def add_like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    newLike = Like(user = user, post=post)
    newLike.save()
    return JsonResponse({"message": "Liked!"})


def edit(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        edit_post = Post.objects.get(pk=post_id)
        edit_post.content = data['content']
        edit_post.save()
        return JsonResponse({"message": "Edit Successful", "data": data['content']})


def index(request):
    #getting all the posts by all the users
    allPosts = Post.objects.all().order_by('id').reverse()

    #Pagination 
    paginator = Paginator(allPosts, 10)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)
    
    allLikes = Like.objects.all()
    #setting up an array of the USERs that the user liked
    whoUserLiked = []
    try:
        for like in allLikes:
            #if the user liked the other user 
            if like.user.id == request.user.id:
                #then we appned their posts
                whoUserLiked.append(like.post.id)
    except:
        whoUserLiked = []

    return render(request, "network/index.html", {
        'allPosts': allPosts,
        'posts_of_the_page': posts_of_the_page,
        'whoUserLiked': whoUserLiked
    })

def new_post(request):
    if request.method == "POST":
        content = request.POST['content']
        #gettin the current user
        user = User.object.get(pk=request.user.id)
        post = Post(content=content, user=user)
        post.save()
        return HttpResponseRedirect(reverse(index))
    
def profile(request, user_id):
    user = User.objects.get(pk=user_id)
    #reversing the posts so that we can show the latest posts first
    allPosts = Post.objects.filter(user=user).order_by('id').reverse()
    
    following = Follow.objects.filter(user=user)
    followers = Follow.objects.filter(user_follower=user)

    try:
        #checking if the current follower is following a particular user
        checkFollow = followers.filter(user=User.objects.get(pk=request.user.id))
        if len(checkFollow) != 0:
            isFollowing = True
        else:
            isFollowing = False
    except:
        isFollowing = False

    #Pagination 
    paginator = Paginator(allPosts, 10)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)
    

    return render(request, "network/profile.html", {
        'allPosts': allPosts,
        'posts_of_the_page': posts_of_the_page,
        'username': user.username,
        'following': following,
        'followers': followers,
        'isFollowing': isFollowing,
        'user_profile': user 
    })

def follow(request):
    #get the user that the user wants to follow
    userfollow = request.POST['userfollow']
    #get all the data of current user
    currentUser = User.objects.get(pk=request.user.id)
    #get all the data of that user that we want to follow
    userFollowData = User.objects.get(username=userfollow)
    #create the follow object and save it so we can follow it officially
    follow = Follow(user=currentUser, user_follower=userFollowData)
    follow.save()
    user_id = userFollowData.id
    #going to that user that we are following
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))

def unfollow(request):
    #get the user that the user wants to unfollow
    userfollow = request.POST['userfollow']
    #get all the data of current user
    currentUser = User.objects.get(pk=request.user.id)
    #get all the data of that user that we want to follow
    userFollowData = User.objects.get(username=userfollow)
    #create the follow object and save it so we can follow it officially
    unfollow = Follow.objects.get(user=currentUser, user_follower=userFollowData)
    unfollow.delete()
    user_id = userFollowData.id
    #going to that user that we are following
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))

def following(request):
    currentUser = User.objects.get(pk=request.user.id)
    #getting all the people/user that the current user follows
    followingPeople = Follow.objects.filter(user=currentUser)
    allPosts = Post.objects.all().order_by('id').reverse()
    
    followingPosts = []
    #for all the post that the current users follows
    for post in allPosts:   
        #for each person in that array 
        for person in followingPeople:
            if person.user_follower == post.user:
                followingPosts.append(post)
    
    #Pagination 
    paginator = Paginator(followingPosts, 10)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)
    

    return render(request, "network/following.html", {
        'allPosts': allPosts,
        'posts_of_the_page': posts_of_the_page
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

