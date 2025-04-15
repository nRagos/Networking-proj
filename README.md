Assignment 1: Networking
This project is a simple P2P torrenting system which showcases networking fundamentals

tracker simply keeps track of clients and serves as a rendezvous point between them
client allows the user to either seed(provide) or leech(receive) files
all other files serve to contribute to these main files

Getting started:
In order to use our system you have to have tqdm installed or run "pip install tqdm" in terminal, this is important aspect of the "gui" donwload progress bar 

Executing the program:
1. Run "python tracker.py" first of all
2. on the seeder machine add all files that you want to seed to the Files directory 
3. next run "python client.py" on terminal and select to be a seeder, this can be done multiple times for many seeders
4. then run "python client.py" on terminal again and select to a leecher and follow the prompts from there
5. leechers are automatically turned into seeders after done leeching
