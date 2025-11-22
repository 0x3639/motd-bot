"""OpenAI-powered message generation for Mr. Kaine MOTD."""
import json
import numpy as np
from typing import List, Optional, Tuple
from openai import OpenAI
from config import Config


class MessageGenerator:
    """Generates daily messages using OpenAI."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.personality = self._load_personality()
        self.posts_context = self._load_posts_context()

    def _load_personality(self) -> str:
        """Load personality guidelines from file."""
        try:
            with open(Config.PERSONALITY_FILE, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: {Config.PERSONALITY_FILE} not found")
            return ""

    def _load_posts_context(self) -> str:
        """Load and format sample posts for context."""
        try:
            with open(Config.POSTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                posts = data.get('posts', [])

                # Sample posts to reduce context size (every 10th post)
                sample_posts = posts[::10][:50]

                context = "Sample posts from Mr. Kaine's Telegram history:\n\n"
                for post in sample_posts:
                    content = post.get('content', '').strip()
                    date = post.get('date', '')
                    if content and len(content) > 20:  # Skip very short posts
                        context += f"[{date}] {content}\n\n"

                return context
        except FileNotFoundError:
            print(f"Warning: {Config.POSTS_FILE} not found")
            return ""
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {Config.POSTS_FILE}")
            return ""

    def generate_message(self, previous_messages: List[str] = None) -> str:
        """
        Generate a new daily message.

        Args:
            previous_messages: List of recent messages to avoid repetition

        Returns:
            Generated message string
        """
        previous_messages = previous_messages or []

        # Build the prompt
        system_prompt = f"""You are Mr. Kaine, creator of Zenon Network.

{self.personality}

Generate a brief daily message with TWO parts:

**Part 1 - Main Message (2-4 sentences):**
- Provide a unique insight, observation, or reflection consistent with your personality
- Rotate through different themes (technical, philosophical, community, critical, visionary)
- Be authentic to your documented voice and positions

**Part 2 - Contributor Thanks (1-2 sentences):**
- Thank those who ACTUALLY DO WORK (not passive participants)
- Focus on: developers, community managers, architects, researchers, shitposters on X
- DO NOT thank node operators (they get emission rewards, mostly do nothing)
- Be genuine, direct, and vary the recognition daily

**FORMAT REQUIREMENT:**
Main message text here.

Thanks to [specific contributor types]. [Genuine appreciation].

CRITICAL: Use a blank line to separate the two parts."""

        user_prompt = f"""Context from your Telegram posts:

{self.posts_context[:3000]}

Recent messages to avoid repetition:
{self._format_recent_messages(previous_messages)}

Generate today's message of the day following the two-part format with a blank line separator."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=300
            )

            message = response.choices[0].message.content.strip()
            return message

        except Exception as e:
            print(f"Error generating message: {e}")
            raise

    def _format_recent_messages(self, messages: List[str], max_messages: int = 10) -> str:
        """Format recent messages for context."""
        if not messages:
            return "None"

        recent = messages[:max_messages]
        formatted = "\n---\n".join(f"- {msg}" for msg in recent)
        return formatted

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            raise

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First embedding vector
            vec2: Second embedding vector

        Returns:
            Similarity score between 0 and 1 (1 = identical, 0 = completely different)
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

    def check_similarity_threshold(
        self,
        message: str,
        recent_embeddings: List[Tuple[str, List[float]]],
        threshold: float = 0.85
    ) -> Tuple[bool, float]:
        """
        Check if message is too similar to recent messages.

        Args:
            message: New message to check
            recent_embeddings: List of (content, embedding) tuples from recent messages
            threshold: Similarity threshold (0-1). Default 0.85 means reject if >85% similar

        Returns:
            Tuple of (is_too_similar, max_similarity_score)
        """
        if not recent_embeddings:
            return False, 0.0

        # Get embedding for new message
        new_embedding = self.get_embedding(message)

        # Calculate similarity to all recent messages
        max_similarity = 0.0
        for content, embedding in recent_embeddings:
            similarity = self.cosine_similarity(new_embedding, embedding)
            max_similarity = max(max_similarity, similarity)

        is_too_similar = max_similarity > threshold
        return is_too_similar, max_similarity

    def validate_message(self, message: str, min_length: int = 50, max_length: int = 800) -> bool:
        """
        Validate generated message meets requirements.

        Args:
            message: The generated message
            min_length: Minimum character length
            max_length: Maximum character length

        Returns:
            True if valid, False otherwise
        """
        if not message:
            return False

        if len(message) < min_length or len(message) > max_length:
            print(f"Message length {len(message)} outside range {min_length}-{max_length}")
            return False

        # Check that message has some substance
        if message.count('.') < 2:  # At least 2 sentences
            print("Message has fewer than 2 sentences")
            return False

        # Check for blank line separator (double newline)
        if '\n\n' not in message:
            print("Message missing blank line separator between main message and thanks")
            return False

        # Check that message doesn't thank node operators
        lower_message = message.lower()
        if 'node operator' in lower_message or 'pillar operator' in lower_message:
            print("Message incorrectly thanks node operators")
            return False

        # Split into parts and validate structure
        parts = message.split('\n\n', 1)
        if len(parts) != 2:
            print("Message doesn't have exactly 2 parts separated by blank line")
            return False

        main_message, thanks = parts

        # Validate main message has content
        if len(main_message.strip()) < 30:
            print("Main message too short")
            return False

        # Validate thanks section exists and has content
        thanks_lower = thanks.lower()
        if not any(keyword in thanks_lower for keyword in ['thanks', 'thank', 'appreciation', 'respect', 'shout']):
            print("Thanks section doesn't contain appreciation keywords")
            return False

        return True

    def generate_with_retry(
        self,
        previous_messages: List[str] = None,
        recent_embeddings: List[Tuple[str, List[float]]] = None,
        max_attempts: int = 3,
        similarity_threshold: float = 0.85
    ) -> Tuple[Optional[str], Optional[List[float]]]:
        """
        Generate message with retry logic and similarity checking.

        Args:
            previous_messages: List of recent messages to avoid repetition
            recent_embeddings: List of (content, embedding) tuples for similarity checking
            max_attempts: Maximum number of generation attempts
            similarity_threshold: Cosine similarity threshold (0-1). Default 0.85

        Returns:
            Tuple of (generated_message, embedding) or (None, None) if all attempts fail
        """
        recent_embeddings = recent_embeddings or []
        best_message = None
        best_embedding = None
        best_similarity = 1.0  # Start with worst case

        for attempt in range(max_attempts):
            try:
                message = self.generate_message(previous_messages)

                # Basic validation
                if not self.validate_message(message):
                    print(f"Attempt {attempt + 1}: Generated message failed validation")
                    continue

                # Similarity check
                if recent_embeddings:
                    is_too_similar, max_similarity = self.check_similarity_threshold(
                        message, recent_embeddings, similarity_threshold
                    )

                    # Track best message even if above threshold
                    if max_similarity < best_similarity:
                        best_similarity = max_similarity
                        best_message = message
                        best_embedding = None  # Will compute if needed

                    if is_too_similar:
                        print(f"Attempt {attempt + 1}: Message too similar (similarity: {max_similarity:.2%})")

                        # On final attempt, use best message we found
                        if attempt == max_attempts - 1 and best_message:
                            print(f"⚠️  Using best message from {max_attempts} attempts (similarity: {best_similarity:.2%})")
                            if not best_embedding:
                                best_embedding = self.get_embedding(best_message)
                            return best_message, best_embedding

                        continue
                    else:
                        print(f"✅ Similarity check passed (max similarity: {max_similarity:.2%})")

                # Get embedding for storage
                embedding = self.get_embedding(message)
                return message, embedding

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                import traceback
                traceback.print_exc()

        # Fallback: If we have a best message, use it even if above threshold
        if best_message:
            print(f"⚠️  All attempts exceeded threshold. Using least similar message (similarity: {best_similarity:.2%})")
            if not best_embedding:
                best_embedding = self.get_embedding(best_message)
            return best_message, best_embedding

        return None, None
