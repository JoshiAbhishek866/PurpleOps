import sys
print("1")
from fastapi import FastAPI, HTTPException
print("2")
from fastapi.middleware.cors import CORSMiddleware
print("3")
from pydantic import BaseModel
print("4")
from src.agents.red_agent import RedAgent
print("5")
from src.agents.blue_agent import BlueAgent
print("6")
import boto3
print("7")
from datetime import datetime
print("8")
from src.config import Config
print("9")
import uuid
import os
from dotenv import load_dotenv
print("10")
from src.core.orchestrator import AgentOrchestrator
print("11")
