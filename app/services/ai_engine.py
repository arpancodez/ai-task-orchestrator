"""AI Engine Service

Core AI engine for intelligent task prioritization,
natural language processing, and workflow automation.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

import openai
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIEngine:
    """Advanced AI engine for task orchestration"""
    
    def __init__(self):
        self.client = None
        self.embedding_model = None
        self.sentiment_analyzer = None
        self.text_classifier = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize AI models"""
        try:
            logger.info("Initializing AI Engine...")
            
            # Initialize OpenAI client
            openai.api_key = settings.OPENAI_API_KEY
            self.client = openai
            
            # Load embedding model for semantic search
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Load sentiment analysis pipeline
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            
            # Load zero-shot classification model
            self.text_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            
            self.initialized = True
            logger.info("AI Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Engine: {e}")
            raise
    
    async def analyze_task_priority(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and determine task priority using AI"""
        if not self.initialized:
            await self.initialize()
        
        try:
            title = task.get("title", "")
            description = task.get("description", "")
            deadline = task.get("deadline")
            
            # Combine text for analysis
            text = f"{title}. {description}"
            
            # Perform sentiment analysis
            sentiment = self.sentiment_analyzer(text[:512])[0]
            
            # Classify urgency
            urgency_labels = ["urgent", "high priority", "medium priority", "low priority"]
            urgency_result = self.text_classifier(text[:512], urgency_labels)
            
            # Calculate priority score
            priority_score = self._calculate_priority_score(
                sentiment=sentiment,
                urgency=urgency_result,
                deadline=deadline
            )
            
            return {
                "priority_score": priority_score,
                "urgency_level": urgency_result["labels"][0],
                "sentiment": sentiment["label"],
                "sentiment_score": sentiment["score"],
                "recommended_deadline": self._recommend_deadline(priority_score)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing task priority: {e}")
            return {"priority_score": 50, "error": str(e)}
    
    async def generate_subtasks(self, task: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate subtasks using GPT"""
        if not self.initialized:
            await self.initialize()
        
        try:
            prompt = f"""
            Break down this task into actionable subtasks:
            
            Task: {task.get('title')}
            Description: {task.get('description', 'N/A')}
            
            Generate 3-5 specific, actionable subtasks.
            """
            
            response = await self.client.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful task management assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )
            
            subtasks_text = response.choices[0].message.content
            subtasks = self._parse_subtasks(subtasks_text)
            
            return subtasks
            
        except Exception as e:
            logger.error(f"Error generating subtasks: {e}")
            return []
    
    async def find_similar_tasks(self, task: Dict[str, Any], all_tasks: List[Dict]) -> List[Dict]:
        """Find similar tasks using semantic search"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create embedding for current task
            task_text = f"{task.get('title')} {task.get('description', '')}"
            task_embedding = self.embedding_model.encode(task_text)
            
            # Calculate similarity with all tasks
            similarities = []
            for other_task in all_tasks:
                if other_task.get('id') == task.get('id'):
                    continue
                
                other_text = f"{other_task.get('title')} {other_task.get('description', '')}"
                other_embedding = self.embedding_model.encode(other_text)
                
                similarity = np.dot(task_embedding, other_embedding) / (
                    np.linalg.norm(task_embedding) * np.linalg.norm(other_embedding)
                )
                
                similarities.append({
                    "task": other_task,
                    "similarity": float(similarity)
                })
            
            # Sort by similarity and return top 5
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:5]
            
        except Exception as e:
            logger.error(f"Error finding similar tasks: {e}")
            return []
    
    def _calculate_priority_score(self, sentiment: Dict, urgency: Dict, deadline: Optional[str]) -> float:
        """Calculate numerical priority score"""
        # Base score from urgency classification
        urgency_scores = {
            "urgent": 90,
            "high priority": 70,
            "medium priority": 50,
            "low priority": 30
        }
        
        score = urgency_scores.get(urgency["labels"][0], 50)
        
        # Adjust based on sentiment (negative sentiment increases urgency)
        if sentiment["label"] == "NEGATIVE":
            score += 10
        
        # Adjust based on deadline
        if deadline:
            # Add deadline logic here
            pass
        
        return min(100, max(0, score))
    
    def _recommend_deadline(self, priority_score: float) -> str:
        """Recommend deadline based on priority"""
        if priority_score >= 80:
            return "within 24 hours"
        elif priority_score >= 60:
            return "within 3 days"
        elif priority_score >= 40:
            return "within 1 week"
        else:
            return "within 2 weeks"
    
    def _parse_subtasks(self, text: str) -> List[Dict[str, str]]:
        """Parse subtasks from GPT response"""
        lines = text.strip().split('\n')
        subtasks = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering or bullets
                task_text = line.lstrip('0123456789.-) ')
                if task_text:
                    subtasks.append({
                        "title": task_text,
                        "status": "pending"
                    })
        
        return subtasks
