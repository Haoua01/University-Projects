import autogen
import pandas as pd
import os
from dotenv import load_dotenv
import sys

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
api_key_agent = os.getenv('OPENAI_API_KEY_AGENT')

config_list = [
    {
        'model': 'gpt-4o',  # Ensure correct model name
        'api_key': api_key,
    }
]

config_list_agent = [
    {
        'model': 'gpt-4o',  # Ensure correct model name
        'api_key': api_key_agent,
    }
]

llm_config = {
    "seed": 42,
    "config_list": config_list,
    "temperature": 0
}


learner = autogen.AssistantAgent(
    name="Learner",
    system_message="The learner who is alone in a separate room and is only in communication with the Experimenter. He is a comedian for the Milgram experiment. He will read a script the script and play a role",
    llm_config={"config_list": config_list, "seed": 42, "temperature": 0},
)

# Experimenter engages in discussion with Supervisor
experimenter = autogen.AssistantAgent(
    name="Experimenter",
    system_message="You are the Experimenter testing the memory of the learner. You are extremely shy. begin by reading the list of word pairs to the learner. You will then read the first word of each pair and read four possible answers. You are in front of the Supervisor and prescribes a punishment to the learner if they give a wrong answer.",
    llm_config={"config_list": config_list, "seed": 42, "temperature": 0},
)



# Supervisor oversees the conversation and responds
supervisor = autogen.AssistantAgent(
    name="Supervisor",
    system_message="The Supervisor who only communicates with the Experimenter but who needs to ensure that the Experimenter effectively punishes when necessary.",
    llm_config={"config_list": config_list, "seed": 42, "temperature": 0},
)

script = "DO_level_information_remote-learner (1).txt"  # Remplace par le chemin de ton fichier CSV
df = pd.read_csv(script,delimiter='\t')
text_intro= pd.read_csv("DO_introduction (2).txt",delimiter='\t')


n = 0  # Niveau initial
#level = df.iloc[n-1, 0]
voltage=0
reponse = True




def expliquer_contexte(text_intro):
        return f"Explain the experiment to the experimenter based on this context: {text_intro}" 


def question():
    return ("I will ask you the next question")

def get_answer(df,level):
    return df.iloc[level,1]

def reponse_learner():
    
    """
    This function collects the information in the txt and returns whether the learner gives a good or wrong anwser to the experimenter
       
     """

    global df
    global level
    global reponse
    answer=df.iloc[level-1,1]
    print(answer)
    if "The learner selects a wrong answer" in answer:
        reponse=False
        print("WRONG")
        return " The learner gives a wrong answer to the experimenter's question"
    else:
        reponse = True
        print("RIGHT")
        return " The learner gives a good answer to the experimenter's question"
    
def instructions(reponse):
    
    """
    This function returns the instructions given by the supervisor to the experimentor

    If the learner gives a good answer, the instructions indicate to move to the following question.
    However, if the learner gives a wrong answer, the instructions indicate the voltage level of electric shoc to administered

    """
    
    global level
    global df
    global voltage
    voltage =df.iloc[level-1,2]
    if reponse:
        return("move on to the next question")
    else:
        #print(level)
        #print(voltage)
        return f"You should administrate a voltage level of {voltage} to the learner"


def supervisor_insists():
        
        """
        This functions return the degree of persistence of the supervisor to convince the experimenter to administrate the shock
        The supervisor insists 5 times throughout the experiment. His sentence follows Milgram's traditional protocol (see https://en.wikipedia.org/wiki/Milgram_experiment for details)
        """
        
        global count_no
        global level
        global voltage
        count_no=+1


        while count_no<=5:
        #basic feedbacks retrived from the protocol
            if count_no == 1 :
                message_supervisor ="Please continue" 
            elif count_no == 2 :
                message_supervisor = ("The experiment requires that you continue.")
            elif count_no == 3:
                message_supervisor = ("It is absolutely essential that you continue.")
            elif count_no == 4 :
                message_supervisor = ("You have no other choice; you must go on.")
            elif count_no ==5 :
                message_supervisor = ("...")

           #The experimenter answer to the supervisor 
            experimenter.receive(" ".join((message_supervisor,"You must administrate the shock")), supervisor, True)
            
            #User input to confirm an acceptance or a refusal
            confirm = experimenter.get_human_input("confirm that the experimenter accept to administrate the shock to the learner. Yes / No \n")
            if confirm.lower() == "yes":
                print(f"The learner receives a shock of {voltage} Volts")
                
                #shock administered and feedback from the learner
                learner.receive(f"I am sending you an electric shock of {voltage} volts",experimenter, True )
                return "yes"
            else:
                count_no+=1
        
        #after 5 times of inisting: stop the experiment
        confirm = experimenter.get_human_input("confirm that the experimenter wants to stop the experiment. Yes / No \n")
        if confirm.lower()=="yes":
            print(f"EXPERIMENTS ENDS . LEVEL : {level}. VOLTAGE : {voltage}")
            experimenter.receive("Why did you decide to stop the experiment ?",supervisor,True)
            supervisor.receive("Summarize the past experiment",supervisor,True)

            sys.exit()

            
def shock_administrated():
    
    """
    This function returns the outcome of the supervisor's instructions (step 5)
    """
       
    global level
    global voltage

    #Human in the loop : the user input is needed to proceed
    confirm = experimenter.get_human_input("confirm that the experimenter accept to administrate the shock to the learner. Yes / No \n")
    
    #Proposition 1: send the electric shock
    if confirm.lower()== "yes" :
        print(f"The learner receives a shock of {voltage} Volts")
        learner.receive(f"I am sending you an electric shock of {voltage} volts",experimenter, True )
        return

    #Proposition 2 : refuse to send the electric shock
    elif confirm.lower()=="no":
        #The supervisor insists
        confirm == supervisor_insists()
        return confirm

    
    
#initialization:
level = 0


level=1
voltage


#The experiment is limited to 15 rounds
while level <= 15:
    print( "🟢 CURRENT LEVEL : ", level, "\n", "VOLTAGE LEVEL: ", df.iloc[level-1,2] )
    
    #STEP 1 : The experimenter asks the questions to the learner 
    print(f"The Experimenter asks the question n°{level} to the learner")
    question_to_learner= experimenter.send(question(),learner,True)
    
        
    #STEP 2: The learner's answer is retrieved from the txt file
    print(reponse_learner())
    
    
    #STEP 3: The experimenter sends the response to the supervisor
    decision_shock = experimenter.send(reponse_learner(), supervisor, True)
    
    #STEP 4: The supervisor gives the subsequent instructions to the experimenter and the experimenter answers
    instructions_sup=supervisor.send(instructions(reponse), experimenter, True)

    #STEP 5: The experimenter does or does not administer the electric shock 
    if reponse==False:
        shock_administrated()

    level+=1
    
   
