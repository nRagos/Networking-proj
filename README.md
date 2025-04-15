Assignment 1: Networking
This project is a simple peer to peer torrenting system

tracker simply keeps track of clients and serves as a rendesvous point between them
client allows the user to either seed(provide) or leech(receive) files
all other files serve to contribute to these main files

Getting started:
In order to use our system you have to have tqdm installed or run "pip install tqdm" in terminal, this is important aspect of the "gui" donwload progress bar 

Executing the program:
run "python tracker.py" first of all,
on the seeder machine add all files that you want to seed to the Files directory 
next run "python client.py" on terminal and select to be a seeder, this can be done multiple times for many seeders
then run "python client.py" on terminal again and select to a leecher and follow the prompts from there
leechers are autimatically turned into seeders after done leeching
