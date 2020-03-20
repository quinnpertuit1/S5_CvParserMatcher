from business.candidate import CandidateBusiness
from business.job_post import JobPostBusiness
from business.matching import Matcher
from numpy import linalg as LA
import services.lang_processing as lp

##################################################


import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import numpy as np
import networkx as nx


client = MongoClient('mongodb+srv://user_imt:2020@s5resumesdb-ppukj.azure.mongodb.net/test')
#print(client.list_database_names())
db = client['db']
#print(db.list_collection_names())

# db_resumeSoveren = db['resumes_sovren']
# recent_resume_post = db_resumeSoveren.find_one({ '_id': ObjectId('5e60f5895a90883323e38bbc') })

# db_jobSoveren = db['jobs_sovren']
# recent_job_post = db_jobSoveren.find_one({ '_id': ObjectId('5e64cbef837ba015d90abc78') })


analysisAxes = [
    {
        'name': 'Skills Match',
        'weight': 1,
        'key_name': 'skills_match',
        'min': None,
        'max': None,
    },
    {
        'name': 'Culture Match',
        'weight': 1,
        'key_name': 'culture_match',
        'min': -1,
        'max': 1,
    }
]

def db_job(db_name,id):
    db_Soveren = db[db_name]
    return db_Soveren.find_one({ '_id': ObjectId(id) })


def candidatePipeline(candidate_id):
    recent_resume_post = db_job('resumes_sovren',candidate_id)
    candidate_business = CandidateBusiness(recent_resume_post)
    candidate_jobdescription,education_dict = candidate_business.download(recent_resume_post)
    candidate_job_dict = candidate_business.getCandidateSkillDict(candidate_jobdescription)
    G3 = candidate_business.getCandidateSkillGraph(candidate_job_dict)
    degree_level = candidate_business.getCandidateEducationDegree(education_dict)
    candidate_unique_skill = candidate_business.getCandidateUnionSkill(candidate_job_dict)
    return G3, degree_level,candidate_unique_skill

def jobPipeline(job_id):
    recent_job_post = db_job('jobs_sovren',job_id)
    job_post_business = JobPostBusiness(recent_job_post)
    job_post_jobdescription,job_education_dict = job_post_business.download(recent_job_post)
    G4 = job_post_business.getJobSkillGraph(job_post_jobdescription)
    degree_level = job_post_business.getJobEducationDegree(job_education_dict)
    job_required_skill = job_post_business.getJobRequiredSkill(recent_job_post)
    return G4 ,degree_level,job_required_skill

# candidatePipeline()



def OnetoOnematching(candidate_id, job_id):
    culture_match, explained_culture_match = None, ''
    candidate_graph, candidate_degree,candidate_unique_skill = candidatePipeline(candidate_id)
    job_graph, job_degree,job_required_skill = jobPipeline(job_id)
    matching = Matcher(candidate_graph,job_graph)
    skills_match = matching.oneToOneAllSkillMatch(candidate_graph,job_graph)
    required_skill_match = matching.getRequiredSkillMatch(job_required_skill,candidate_unique_skill)
    #model = lp.getGloveModel(300)
    #explained_culture_match, culture_match = matching.getOneToOneCultureMatch(candidate_id, job_id, model, db['resumes_sovren'], db['jobs_sovren'])
    string_education_match, _, _ = matching.educationDegreeMatch(candidate_degree,job_degree)
    return {
        'skills_match': skills_match,
        'culture_match': culture_match,
        'required_skill_match': required_skill_match, 
        'string_education_match': string_education_match, 
        'explained_culture_match': explained_culture_match,
        }



def OnetoManymatching(candidate_id, job_id):
    candidateGraph = []
    job_graph = jobPipeline(job_id)
    for position in range(len(candidate_id)):
        candidateGraph.append(candidatePipeline(candidate_id[position]))
    matching = Matcher(candidateGraph,job_graph)
    return matching.onetoManyAllSkillMatch(candidateGraph,job_graph)

# print('One to one matching of CV to the jobpost is ',OnetoOnematching('5e60f5895a90883323e38bbc','5e64cbef837ba015d90abc78'))

# print('One to one matching of CV to the jobpost is ',OnetoManymatching(['5e60f5895a90883323e38bbc','5e60f5895a90883323e38bbc'],'5e64cbef837ba015d90abc76'))


################################################################################################
#education System


def runOneToOne(candidate_id, job_id, explainable=False):
    otom_res = OnetoOnematching(candidate_id, job_id)
    #skills_match, culture_match, required_skill_match, string_education_match, explained_culture_match = 
    print('\n==========================')
    print('\n======== RESULT ==========')
    if explainable: print(otom_res['explained_culture_match'])
    print(f"Overall Culture Matching: {otom_res['culture_match']} %")
    print(otom_res['string_education_match'])
    print(f"OverAllSkills Matching: {otom_res['skills_match']} %")
    print(f"Required Skill Matching: {otom_res['required_skill_match']} %")
    return otom_res

#runOneToOne('5e60f5895a90883323e38bbc','5e64cbef837ba015d90abc78', True)


# print('One to one matching of CV to the jobpost is ',OnetoManymatching(['5e60f5895a90883323e38bbc','5e60f5895a90883323e38bbc'],'5e64cbef837ba015d90abc76'))