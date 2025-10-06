"""Games cog: various educational and fun games with leaderboard"""
from discord.ext import commands
import discord
import json
from discord import Embed, app_commands
from pathlib import Path
from utils.helper import async_load_json, async_save_json
import random
import asyncio
import time
import string


DATA_PATH = Path(__file__).parent.parent / 'data' / 'games.json'
BANK_PATH = Path(__file__).parent.parent / 'data' / 'games_bank.json'

# Game utilities
MEMORY_EMOJIS = ['🌟', '🎈', '🎨', '🎭', '🎪', '🎯', '🎲', '🎰', '🎳', '🎼', '🎵', '🎹', '🎸', '🎮', '🎲']
WORD_LIST = ['python', 'coding', 'algorithm', 'programming', 'computer', 'software', 'developer', 'learning']
MATH_OPERATORS = ['+', '-', '*']

# Load game content from bank
TRUTH = [
    "What's a study habit you wish you had?",
    "What's the hardest subject for you?",
]
DARE = [
    "Do 10 jumping jacks and post a selfie (optional).",
    "Explain a topic you're studying to someone in 60 seconds.",
]

# Game response templates
GAME_WIN = [
    "🎉 Congratulations! You won!",
    "🌟 Amazing job!",
    "🏆 Victory is yours!",
    "⭐ Well played!"
]

GAME_LOSE = [
    "Better luck next time!",
    "Don't give up - try again!",
    "So close! Want another try?",
    "Keep practicing!"
]



class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = {'leaderboard': {}, 'game_scores': {}, 'quiz_history': {}}
        self.current_quiz = {}
        bot.loop.create_task(self.load_data())
        
    async def show_quiz_results(self, ctx, user_id: int, questions, answers, score: int):
        """Show detailed quiz results in an embed"""
        embed = discord.Embed(title="Quiz Results", color=discord.Color.blue())
        
        # Add score and stats
        embed.add_field(name="Final Score", value=f"{score}/100", inline=True)
        correct = sum(1 for q, a in zip(questions, answers) if q['a'] == a)
        embed.add_field(name="Correct Answers", value=f"{correct}/{len(questions)}", inline=True)
        
        # Show question review
        review = []
        for i, (q, a) in enumerate(zip(questions, answers), 1):
            mark = '✅' if a == q['a'] else '❌'
            your_ans = 'No answer' if a is None else q['choices'][a-1]
            correct_ans = q['choices'][q['a']-1]
            review.append(f"{mark} Q{i}: {q['q']}\nYour answer: {your_ans}\nCorrect: {correct_ans}")
        
        # Split review into fields if needed
        chunks = [review[i:i+3] for i in range(0, len(review), 3)]
        for i, chunk in enumerate(chunks):
            embed.add_field(name=f"Questions {i*3+1}-{i*3+len(chunk)}", 
                          value='\n\n'.join(chunk), inline=False)
        
        # Add to user's quiz history
        if str(user_id) not in self.data['quiz_history']:
            self.data['quiz_history'][str(user_id)] = []
        self.data['quiz_history'][str(user_id)].append({
            'score': score,
            'correct': correct,
            'total': len(questions),
            'timestamp': time.time()
        })
        await async_save_json(DATA_PATH, self.data)
        
        # Show quiz leaderboard
        quiz_scores = []
        for uid, scores in self.data.get('game_scores', {}).items():
            if 'quiz' in scores:
                quiz_scores.append((uid, scores['quiz']))
        
        if quiz_scores:
            quiz_scores.sort(key=lambda x: x[1], reverse=True)
            leaderboard = []
            for i, (uid, score) in enumerate(quiz_scores[:5], 1):
                user = self.bot.get_user(int(uid))
                name = user.display_name if user else 'Unknown'
                leaderboard.append(f"{i}. {name}: {score}")
            
            embed.add_field(name="Quiz Leaderboard (Top 5)", 
                          value='\n'.join(leaderboard), inline=False)
        
        await ctx.send(embed=embed)

    async def load_data(self):
        try:
            self.data = await async_load_json(DATA_PATH)
            if 'game_scores' not in self.data:
                self.data['game_scores'] = {}
                await async_save_json(DATA_PATH, self.data)
        except FileNotFoundError:
            await async_save_json(DATA_PATH, self.data)

    async def update_score(self, user_id: int, game: str, score: int):
        """Update a user's score for a specific game"""
        if str(user_id) not in self.data['game_scores']:
            self.data['game_scores'][str(user_id)] = {}
        if game not in self.data['game_scores'][str(user_id)]:
            self.data['game_scores'][str(user_id)][game] = 0
        self.data['game_scores'][str(user_id)][game] += score
        await async_save_json(DATA_PATH, self.data)
        
    async def show_game_stats(self, ctx, user_id: int, game: str, score: int, additional_fields: dict = None):
        """Show game statistics in an embed"""
        embed = discord.Embed(title=f"🎮 {game.replace('-', ' ').title()}", color=discord.Color.blue())
        embed.add_field(name="Score", value=str(score), inline=True)
        
        # Add total score for this game type
        total_score = self.data['game_scores'].get(str(user_id), {}).get(game, 0)
        embed.add_field(name="Total Score", value=str(total_score), inline=True)
        
        # Add any additional fields
        if additional_fields:
            for name, value in additional_fields.items():
                embed.add_field(name=name, value=value, inline=False)
                
        embed.set_footer(text=f"Play more games to improve your score!")
        await ctx.send(embed=embed)
        
    def generate_board(self, size=3):
        """Generate a board for games like tic-tac-toe"""
        return [[' ' for _ in range(size)] for _ in range(size)]
        
    def format_board(self, board):
        """Format a board for display"""
        rows = []
        for i, row in enumerate(board):
            formatted_row = []
            for j, cell in enumerate(row):
                if cell == ' ':
                    formatted_row.append('⬜')
                elif cell == 'X':
                    formatted_row.append('❌')
                elif cell == 'O':
                    formatted_row.append('⭕')
                else:
                    formatted_row.append(cell)
            rows.append(' '.join(formatted_row))
        return '\n'.join(rows)
        
    def check_win(self, board, player):
        """Check if a player has won on the board"""
        size = len(board)
        # Check rows and columns
        for i in range(size):
            if all(board[i][j] == player for j in range(size)) or \
               all(board[j][i] == player for j in range(size)):
                return True
        # Check diagonals
        if all(board[i][i] == player for i in range(size)) or \
           all(board[i][size-1-i] == player for i in range(size)):
            return True
        return False

    @commands.hybrid_command(name='memory-match', description='Play memory matching game')
    async def memory_match(self, ctx):
        """Play a memory matching game with emojis"""
        # Generate pairs of emojis
        pairs = random.sample(MEMORY_EMOJIS, 6) * 2
        random.shuffle(pairs)
        board = [pairs[i:i+3] for i in range(0, 12, 3)]
        hidden = [['⬛' for _ in range(3)] for _ in range(4)]
        
        # Show initial board
        msg = await ctx.send(f"Memory Match Game:\n{self.format_board(hidden)}")
        await asyncio.sleep(1)
        
        moves = 0
        matched = 0
        first = None
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
            
        while matched < 6:
            try:
                # Get player move
                await ctx.send("Enter row,col (e.g. 1,2):")
                response = await self.bot.wait_for('message', check=check, timeout=30)
                
                try:
                    row, col = map(lambda x: int(x.strip())-1, response.content.split(','))
                    if not (0 <= row < 4 and 0 <= col < 3) or hidden[row][col] != '⬛':
                        await ctx.send("Invalid move! Try again.")
                        continue
                except:
                    await ctx.send("Invalid format! Use row,col (e.g. 1,2)")
                    continue
                    
                # Reveal card
                hidden[row][col] = board[row][col]
                await msg.edit(content=f"Memory Match Game:\n{self.format_board(hidden)}")
                
                if first is None:
                    first = (row, col)
                else:
                    moves += 1
                    r, c = first
                    if board[r][c] == board[row][col]:
                        matched += 1
                        await ctx.send("✅ Match found!")
                    else:
                        await asyncio.sleep(1)
                        hidden[r][c] = hidden[row][col] = '⬛'
                        await msg.edit(content=f"Memory Match Game:\n{self.format_board(hidden)}")
                    first = None
                    
            except asyncio.TimeoutError:
                await ctx.send("Game timed out!")
                return
                
        score = int((6 / moves) * 100)
        await self.update_score(ctx.author.id, 'memory-match', score)
        await self.show_game_stats(ctx, ctx.author.id, 'memory-match', score, 
                                  {"Moves": moves, "Pairs Found": matched})
                
    @commands.hybrid_command(name='word-scramble', description='Unscramble the word')
    async def word_scramble(self, ctx):
        """Play a word scramble game"""
        word = random.choice(WORD_LIST)
        scrambled = ''.join(random.sample(word, len(word)))
        
        await ctx.send(f"Unscramble this word: **{scrambled}**")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
            
        try:
            start_time = time.time()
            msg = await self.bot.wait_for('message', check=check, timeout=30)
            
            if msg.content.lower() == word:
                duration = time.time() - start_time
                score = int(max(0, 100 - duration * 2))
                await self.update_score(ctx.author.id, 'word-scramble', score)
                await self.show_game_stats(ctx, ctx.author.id, 'word-scramble', score,
                                          {"Time": f"{duration:.1f}s", "Word": word})
            else:
                await ctx.send(f"Sorry, the word was **{word}**")
                
        except asyncio.TimeoutError:
            await ctx.send(f"Time's up! The word was **{word}**")
            
    def generate_math_question(self, difficulty):
        """Generate a math question based on difficulty level"""
        if difficulty == "easy":
            num1 = random.randint(1, 20)
            num2 = random.randint(1, 20)
            op = random.choice(['+', '-', '*'])
        elif difficulty == "medium":
            num1 = random.randint(10, 50)
            num2 = random.randint(10, 50)
            op = random.choice(['+', '-', '*', '/'])
            if op == '/':  # Ensure clean division
                num1 = num2 * random.randint(1, 10)
        elif difficulty == "hard":
            if random.choice([True, False]):
                # Complex arithmetic
                num1 = random.randint(20, 100)
                num2 = random.randint(20, 100)
                op = random.choice(['+', '-', '*', '/'])
                if op == '/':
                    num1 = num2 * random.randint(1, 20)
            else:
                # Square/cube
                num1 = random.randint(2, 20)
                num2 = random.choice([2, 3])  # Square or cube
                return f"{num1}^{num2} = ?", num1 ** num2
        else:  # extreme
            ops = random.randint(2, 3)  # 2-3 operations
            nums = [random.randint(10, 50) for _ in range(ops + 1)]
            operators = random.choices(['+', '-', '*'], k=ops)
            question = str(nums[0])
            expression = str(nums[0])
            for i in range(ops):
                question += f" {operators[i]} {nums[i+1]}"
                expression += f" {operators[i]} {nums[i+1]}"
            return f"{question} = ?", eval(expression)

        # Generate basic question
        question = f"{num1} {op} {num2} = ?"
        if op == '/':
            answer = num1 // num2  # Integer division
        else:
            answer = eval(f"{num1} {op} {num2}")
        return question, answer

    @commands.hybrid_command(name='math-challenge', description='Solve math problems')
    async def math_challenge(self, ctx):
        """Play a math challenge game with increasing difficulty"""
        correct = 0
        total_time = 0
        questions = []
        user_answers = []
        
        embed = discord.Embed(
            title="🧮 Advanced Math Challenge",
            description="Get ready for 20 questions of increasing difficulty!",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Difficulty Levels",
            value="Questions 1-5: Easy\nQuestions 6-10: Medium\n"
                  "Questions 11-15: Hard\nQuestions 16-20: Extreme",
            inline=False
        )
        embed.add_field(
            name="Scoring",
            value="Easy: 3 points\nMedium: 5 points\n"
                  "Hard: 8 points\nExtreme: 10 points",
            inline=False
        )
        await ctx.send(embed=embed)
        await asyncio.sleep(2)
        
        # Generate questions for each difficulty
        difficulties = ['easy'] * 5 + ['medium'] * 5 + ['hard'] * 5 + ['extreme'] * 5
        points = {'easy': 3, 'medium': 5, 'hard': 8, 'extreme': 10}
        total_points = 0
        
        for i, difficulty in enumerate(difficulties, 1):
            question, answer = self.generate_math_question(difficulty)
            questions.append((question, answer, difficulty))
            
            # Create question embed
            q_embed = discord.Embed(
                title=f"Question {i}/20 - {difficulty.upper()}",
                description=question,
                color=discord.Color.green()
            )
            q_embed.set_footer(text=f"Worth {points[difficulty]} points | Time limit: 30 seconds")
            await ctx.send(embed=q_embed)
            
            try:
                start_time = time.time()
                msg = await self.bot.wait_for('message', 
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                    timeout=30
                )
                
                duration = time.time() - start_time
                total_time += duration
                
                try:
                    user_answer = int(msg.content)
                    user_answers.append(user_answer)
                    if user_answer == answer:
                        correct += 1
                        total_points += points[difficulty]
                        await ctx.send(f"✅ Correct! +{points[difficulty]} points")
                    else:
                        await ctx.send(f"❌ Wrong! The answer was {answer}")
                except ValueError:
                    await ctx.send("That's not a number!")
                    user_answers.append(None)
                    
            except asyncio.TimeoutError:
                await ctx.send(f"⏰ Time's up! The answer was {answer}")
                user_answers.append(None)
                
        # Calculate final results
        avg_time = total_time / 20 if total_time > 0 else 30
        
        # Create results embed
        embed = discord.Embed(
            title="🏆 Math Challenge Results",
            description=f"Total Points: **{total_points}**",
            color=discord.Color.blue()
        )
        
        # Add stats per difficulty
        for diff in ['easy', 'medium', 'hard', 'extreme']:
            diff_questions = [(q, a, u) for (q, a, d), u in zip(questions, user_answers) if d == diff]
            correct_diff = sum(1 for _, a, u in diff_questions if u == a)
            embed.add_field(
                name=f"{diff.title()} Level",
                value=f"Correct: {correct_diff}/5\nPoints: {correct_diff * points[diff]}/{5 * points[diff]}",
                inline=True
            )
        
        embed.add_field(name="Total Correct", value=f"{correct}/20", inline=True)
        embed.add_field(name="Avg Time/Question", value=f"{avg_time:.1f}s", inline=True)
        
        # Show question review grouped by difficulty
        for diff in ['easy', 'medium', 'hard', 'extreme']:
            review = []
            diff_questions = [(q, a, u) for (q, a, d), u in zip(questions, user_answers) if d == diff]
            for i, (q, a, u) in enumerate(diff_questions, 1):
                mark = '✅' if u == a else '❌'
                review.append(f"{mark} Q{i}: {q}\nYour answer: {u if u is not None else 'timeout'} (Correct: {a})")
            if review:
                embed.add_field(
                    name=f"{diff.title()} Questions Review",
                    value='\n'.join(review),
                    inline=False
                )
                
        # Update total score
        final_score = int((total_points / 130) * 100)  # Max points: 130
        await self.update_score(ctx.author.id, 'math-challenge', final_score)
        
        await ctx.send(embed=embed)
        
    @commands.hybrid_command(name='leaderboard', description='Show game leaderboards')
    async def show_leaderboard(self, ctx: commands.Context, game: str = None):
        """Show the leaderboard for all games or a specific game"""
        if not self.data['game_scores']:
            await ctx.send("No game scores recorded yet!")
            return

        if game and game.lower() not in ["memory-match", "word-scramble", "math-challenge", 
                                       "typing-speed-test", "emoji-quiz", "fastest-finger", 
                                       "connect-4", "tic-tac-toe"]:
            games_list = ["memory-match", "word-scramble", "math-challenge", "typing-speed-test", 
                         "emoji-quiz", "fastest-finger", "connect-4", "tic-tac-toe"]
            await ctx.send(f"Invalid game! Available games: {', '.join(games_list)}")
            return

        embed = discord.Embed(title="🏆 Game Leaderboard", color=discord.Color.gold())
        
        if game:
            # Show leaderboard for specific game
            scores = []
            for user_id, games in self.data['game_scores'].items():
                if game in games:
                    scores.append((user_id, games[game]))
            
            if not scores:
                await ctx.send(f"No scores recorded for {game} yet!")
                return

            scores.sort(key=lambda x: x[1], reverse=True)
            leaderboard = ""
            for i, (user_id, score) in enumerate(scores[:10], 1):
                user = self.bot.get_user(int(user_id)) or "Unknown User"
                leaderboard += f"{i}. {user}: {score} points\n"
            
            embed.add_field(name=f"{game} Leaderboard", value=leaderboard or "No scores yet!")

        else:
            # Show top players across all games
            total_scores = {}
            for user_id, games in self.data['game_scores'].items():
                total_scores[user_id] = sum(games.values())

            scores = sorted(total_scores.items(), key=lambda x: x[1], reverse=True)
            leaderboard = ""
            for i, (user_id, score) in enumerate(scores[:10], 1):
                user = self.bot.get_user(int(user_id)) or "Unknown User"
                leaderboard += f"{i}. {user}: {score} points\n"
            
            embed.add_field(name="Overall Leaderboard", value=leaderboard or "No scores yet!")

        await ctx.send(embed=embed)

    async def cog_load(self):
        self.data = await async_load_json(DATA_PATH, default={'leaderboard': {}})
        # Load banks if available
        if BANK_PATH.exists():
            try:
                bank = await async_load_json(BANK_PATH, default={})
                if bank:
                    global TRUTH, DARE
                    TRUTH = bank.get('truths', TRUTH)
                    DARE = bank.get('dares', DARE)
                    # if there's a large quiz bank, store it in memory
                    self.quiz_bank = bank.get('quiz', [])
                else:
                    self.quiz_bank = []
            except Exception:
                self.quiz_bank = []
        else:
            self.quiz_bank = []

    @commands.hybrid_command(name='guess-number', description='Guess the number game')
    async def guess_number(self, ctx):
        """Play a number guessing game"""
        number = random.randint(1, 100)
        attempts = 0
        max_attempts = 7
        
        await ctx.send("I'm thinking of a number between 1 and 100. You have 7 attempts!")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
            
        while attempts < max_attempts:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30)
                
                try:
                    guess = int(msg.content)
                    attempts += 1
                    
                    if guess == number:
                        score = int((1 - (attempts-1)/max_attempts) * 100)
                        await self.update_score(ctx.author.id, 'guess-number', score)
                        await self.show_game_stats(ctx, ctx.author.id, 'guess-number', score,
                                                  {"Attempts": attempts, "Number": number})
                        return
                    elif guess < number:
                        await ctx.send(f"Higher! ({max_attempts - attempts} attempts left)")
                    else:
                        await ctx.send(f"Lower! ({max_attempts - attempts} attempts left)")
                        
                except ValueError:
                    await ctx.send("That's not a valid number!")
                    continue
                    
            except asyncio.TimeoutError:
                await ctx.send(f"Game over! The number was {number}")
                return
                
        await ctx.send(f"Out of attempts! The number was {number}")
        await self.update_score(ctx.author.id, 'guess-number', 10)
        
    @commands.hybrid_command(name='emoji-quiz', description='Guess the emoji description')
    async def emoji_quiz(self, ctx):
        """Play an emoji quiz game"""
        emojis = {
            '💻': ['computer', 'laptop', 'pc'],
            '📖': ['book', 'textbook', 'novel'],
            '🍎': ['apple', 'red apple', 'fruit'],
            '🎸': ['guitar', 'music', 'instrument'],
            '🚗': ['car', 'automobile', 'vehicle'],
            '⚽': ['football', 'soccer', 'ball'],
            '🍕': ['pizza', 'food', 'slice'],
            '🐻': ['bear', 'teddy', 'animal']
        }
        
        emoji, answers = random.choice(list(emojis.items()))
        
        embed = discord.Embed(title="Emoji Quiz", color=discord.Color.blue())
        embed.add_field(name="Guess what this represents", value=emoji, inline=False)
        embed.add_field(name="Instructions", value="Type your answer. Multiple answers may be correct!", inline=False)
        
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
            
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30)
            answer = msg.content.lower()
            
            if answer in answers:
                score = 100
                await self.update_score(ctx.author.id, 'emoji-quiz', score)
                await self.show_game_stats(ctx, ctx.author.id, 'emoji-quiz', score,
                                          {"Correct Answer": answers[0], "Your Answer": answer})
            else:
                await ctx.send(f"Not quite! The answer was: {answers[0]}")
                
        except asyncio.TimeoutError:
            await ctx.send(f"Time's up! The answer was: {answers[0]}")
    
    def _get_related_questions(self, current_q, questions, num=2):
        """Get related follow-up questions based on keywords"""
        words = set(current_q.lower().split())
        related = []
        for q in questions:
            if q == current_q:
                continue
            q_words = set(q.lower().split())
            common = len(words & q_words)
            if common > 0:
                related.append((common, q))
        related.sort(reverse=True)
        return [q for _, q in related[:num]]

    @commands.hybrid_command(name='truth', description='Random truth question')
    async def truth(self, ctx):
        """Get a random truth question with follow-ups"""
        question = random.choice(TRUTH)
        
        embed = discord.Embed(
            title="🤔 Truth Question",
            description=question,
            color=discord.Color.blue()
        )
        
        # Get follow-up questions
        followups = self._get_related_questions(question, TRUTH)
        if followups:
            embed.add_field(
                name="👉 Follow-up Questions",
                value="\n".join(f"• {q}" for q in followups),
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='dare', description='Random dare challenge')
    async def dare(self, ctx):
        """Get a random dare challenge with follow-ups"""
        dare_task = random.choice(DARE)
        
        embed = discord.Embed(
            title="💪 Dare Challenge",
            description=dare_task,
            color=discord.Color.red()
        )
        
        # Get related dares
        related = self._get_related_questions(dare_task, DARE)
        if related:
            embed.add_field(
                name="🎯 Alternative Challenges",
                value="\n".join(f"• {d}" for d in related),
                inline=False
            )
            
        await ctx.send(embed=embed)

    @commands.hybrid_group(name='quiz', invoke_without_command=True)
    async def quiz(self, ctx):
        """Quiz commands and leaderboard"""
        await ctx.send('Use subcommands: start, leaderboard')

    @quiz.command(name='start', description='Start a mini quiz')
    async def quiz_start(self, ctx):
        """Start a new quiz game"""
        user = ctx.author
        channel = ctx.channel

        await ctx.send('Starting quiz... I will post questions here. Reply with your answers as messages.')
        # run quiz asynchronously
        self.bot.loop.create_task(self._run_quiz_for_user(user, channel))

    async def _run_quiz_for_user(self, user: discord.User, channel: discord.abc.Messageable):
        # Load questions from games_bank.json
        try:
            with open('data/games_bank.json', 'r') as f:
                games_bank = json.load(f)
                questions = random.sample(games_bank['quiz'], min(10, len(games_bank['quiz'])))
        except Exception as e:
            await channel.send(f'Error loading quiz questions: {str(e)}')
            return

        score = 0
        total_time = 0
        correct_answers = []
        wrong_answers = []

        def check(m: discord.Message):
            return m.author.id == user.id and m.channel.id == getattr(channel, 'id', None)

        for q in questions:
            embed = Embed(title='Quiz', description=q['q'])
            for i, c in enumerate(q['choices'], start=1):
                embed.add_field(name=str(i), value=c, inline=False)
            try:
                await channel.send(embed=embed)
            except Exception:
                # channel might be a DM channel or have send disabled
                try:
                    dm = await user.create_dm()
                    channel = dm
                    await channel.send(embed=embed)
                except Exception:
                    # give up on this question
                    continue

            start_time = time.time()
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30)
                answer_time = time.time() - start_time
                total_time += answer_time
                
                choice = int(msg.content.strip())
                is_correct = choice == q['a']
                
                # Create feedback embed
                feedback = discord.Embed(
                    title="Question Result",
                    color=discord.Color.green() if is_correct else discord.Color.red()
                )
                feedback.add_field(name="Your Answer", value=q['choices'][choice-1], inline=True)
                feedback.add_field(name="Correct Answer", value=q['choices'][q['a']-1], inline=True)
                feedback.add_field(name="Time Taken", value=f"{answer_time:.1f}s", inline=True)
                
                if is_correct:
                    score += 1
                    correct_answers.append((q['q'], answer_time))
                    feedback.description = "✅ Correct! Well done!"
                else:
                    wrong_answers.append((q['q'], q['choices'][q['a']-1]))
                    feedback.description = "❌ Incorrect. Keep trying!"
                
                await channel.send(embed=feedback)
                
            except asyncio.TimeoutError:
                await channel.send('⏰ Time\'s up! Moving to next question...')
            except ValueError:
                await channel.send('❌ Invalid input! Please enter a number between 1 and 4.')

        # reward and store leaderboard & stats
        points = random.randint(1, 5)
        uid = str(user.id)
        
        # Update leaderboard
        lb = self.data.setdefault('leaderboard', {})
        lb[uid] = lb.get(uid, 0) + points
        
        # Update detailed stats
        stats = self.data.setdefault('quiz_stats', {})
        user_stats = stats.setdefault(uid, {
            'quizzes': [],
            'total_questions': 0,
            'correct_answers': 0,
            'fastest_answer': float('inf'),
            'accuracy': 0
        })
        
        # Add this quiz's stats
        quiz_result = {
            'timestamp': time.time(),
            'score': score,
            'total_time': total_time,
            'avg_time': total_time / len(questions),
            'questions': len(questions)
        }
        user_stats['quizzes'].append(quiz_result)
        user_stats['total_questions'] += len(questions)
        user_stats['correct_answers'] += score
        
        # Update fastest answer time
        if correct_answers:
            fastest_this_quiz = min(t for _, t in correct_answers)
            user_stats['fastest_answer'] = min(fastest_this_quiz, user_stats['fastest_answer'])
        
        # Update accuracy
        total_questions = user_stats['total_questions']
        if total_questions > 0:
            user_stats['accuracy'] = (user_stats['correct_answers'] / total_questions) * 100
        
        try:
            await async_save_json(DATA_PATH, self.data)
        except Exception as e:
            print(f"Error saving quiz stats: {e}")

        # Create final results embed
        results = discord.Embed(
            title="📊 Quiz Results",
            description=f"Final Score: {score}/{len(questions)} | +{points} points",
            color=discord.Color.blue()
        )
        
        # Add performance stats
        accuracy = (score / len(questions)) * 100
        avg_time = total_time / len(questions)
        results.add_field(name="Accuracy", value=f"{accuracy:.1f}%", inline=True)
        results.add_field(name="Average Time", value=f"{avg_time:.1f}s per question", inline=True)
        results.add_field(name="Total Time", value=f"{total_time:.1f}s", inline=True)
        
        # Add performance breakdown
        if correct_answers:
            fastest = min(correct_answers, key=lambda x: x[1])
            results.add_field(
                name="🏃 Fastest Correct Answer",
                value=f"Q: {fastest[0]}\nTime: {fastest[1]:.1f}s",
                inline=False
            )
            
        if wrong_answers:
            wrong_list = "\n".join([f"Q: {q}\nA: {a}" for q, a in wrong_answers[:3]])
            results.add_field(
                name="📝 Questions to Review",
                value=wrong_list if wrong_list else "None",
                inline=False
            )
            
        try:
            await channel.send(user.mention, embed=results)
        except Exception:
            try:
                dm = await user.create_dm()
                await dm.send(embed=results)
            except Exception:
                pass

    @quiz.command(name='leaderboard')
    async def quiz_leaderboard(self, ctx, category: str = None):
        """Show the quiz leaderboard with optional category filter"""
        lb = self.data.get('leaderboard', {})
        stats = self.data.get('quiz_stats', {})
        
        if not lb:
            await ctx.send('No leaderboard yet.')
            return
            
        embed = discord.Embed(
            title='📊 Quiz Leaderboard',
            color=discord.Color.blue()
        )
        
        # Add global stats
        total_quizzes = sum(len(stats.get(uid, {}).get('quizzes', [])) for uid in lb)
        total_questions = sum(stats.get(uid, {}).get('total_questions', 0) for uid in lb)
        avg_accuracy = sum(stats.get(uid, {}).get('accuracy', 0) for uid in lb) / len(lb) if lb else 0
        
        embed.add_field(name="Total Quizzes Taken", value=str(total_quizzes), inline=True)
        embed.add_field(name="Questions Answered", value=str(total_questions), inline=True)
        embed.add_field(name="Average Accuracy", value=f"{avg_accuracy:.1f}%", inline=True)
        
        # Sort and filter players
        items = sorted(lb.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Format leaderboard with detailed stats
        leaderboard = []
        for i, (uid, pts) in enumerate(items, 1):
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else uid
            
            user_stats = stats.get(uid, {})
            accuracy = user_stats.get('accuracy', 0)
            quizzes = len(user_stats.get('quizzes', []))
            fastest = user_stats.get('fastest_answer', 0)
            
            entry = (
                f"**{i}.** __{name}__\n"
                f"Points: **{pts}** | Accuracy: **{accuracy:.1f}%**\n"
                f"Quizzes: {quizzes} | Best Time: {fastest:.1f}s"
            )
            leaderboard.append(entry)
            
        embed.description = '\n\n'.join(leaderboard) if leaderboard else 'No scores yet!'
        
        # Add time period note
        embed.set_footer(text='Leaderboard updates after each quiz completed')
        await ctx.send(embed=embed)


    @commands.hybrid_command(name='typing-speed', description='Test your typing speed')
    async def typing_speed(self, ctx):
        """Test your typing speed"""
        sentences = [
            "The quick brown fox jumps over the lazy dog.",
            "Python is a powerful programming language.",
            "Practice makes perfect when learning to code.",
            "Algorithms help solve complex problems efficiently."
        ]
        sentence = random.choice(sentences)
        
        embed = discord.Embed(title="Typing Speed Test", color=discord.Color.blue())
        embed.add_field(name="Type this sentence", value=f"```{sentence}```", inline=False)
        embed.add_field(name="Instructions", value="Timer starts when you start typing. Be accurate!", inline=False)
        
        await ctx.send(embed=embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
            
        try:
            start_time = time.time()
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            end_time = time.time()
            
            duration = end_time - start_time
            typed = msg.content
            
            # Calculate WPM and accuracy
            words = len(sentence.split())
            wpm = int((words / duration) * 60)
            
            # Calculate accuracy
            correct_chars = sum(1 for a, b in zip(sentence, typed) if a == b)
            accuracy = int((correct_chars / len(sentence)) * 100)
            
            # Calculate score based on WPM and accuracy
            score = int((wpm * accuracy) / 100)
            
            await self.update_score(ctx.author.id, 'typing-speed', score)
            await self.show_game_stats(ctx, ctx.author.id, 'typing-speed', score,
                                      {"WPM": wpm, "Accuracy": f"{accuracy}%", 
                                       "Time": f"{duration:.1f}s"})
            
        except asyncio.TimeoutError:
            await ctx.send("Time's up!")
            
    @commands.hybrid_command(name='tic-tac-toe', description='Play Tic-tac-toe')
    async def tictactoe(self, ctx):
        """Play Tic-tac-toe against the bot"""
        board = self.generate_board(3)
        player = 'X'
        bot_char = 'O'
        
        # Show initial board
        msg = await ctx.send(f"Tic-tac-toe\nYour move (row,col):\n{self.format_board(board)}")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
            
        while True:
            try:
                # Player move
                response = await self.bot.wait_for('message', check=check, timeout=30)
                try:
                    row, col = map(lambda x: int(x.strip())-1, response.content.split(','))
                    if not (0 <= row < 3 and 0 <= col < 3) or board[row][col] != ' ':
                        await ctx.send("Invalid move! Try again.")
                        continue
                except:
                    await ctx.send("Invalid format! Use row,col (e.g. 1,2)")
                    continue
                    
                board[row][col] = player
                if self.check_win(board, player):
                    await msg.edit(content=f"You win!\n{self.format_board(board)}")
                    await self.update_score(ctx.author.id, 'tic-tac-toe', 100)
                    return
                    
                # Bot move
                moves = [(i, j) for i in range(3) for j in range(3) if board[i][j] == ' ']
                if not moves:
                    await msg.edit(content=f"It's a draw!\n{self.format_board(board)}")
                    await self.update_score(ctx.author.id, 'tic-tac-toe', 50)
                    return
                    
                bot_row, bot_col = random.choice(moves)
                board[bot_row][bot_col] = bot_char
                await msg.edit(content=f"Your move (row,col):\n{self.format_board(board)}")
                
                if self.check_win(board, bot_char):
                    await msg.edit(content=f"Bot wins!\n{self.format_board(board)}")
                    await self.update_score(ctx.author.id, 'tic-tac-toe', 25)
                    return
                    
            except asyncio.TimeoutError:
                await ctx.send("Game timed out!")
                return
                
    @commands.hybrid_command(name='rps', description='Play rock-paper-scissors with the bot')
    @app_commands.describe(
        choice='Your move: rock, paper, or scissors'
    )
    @app_commands.choices(choice=[
        app_commands.Choice(name='Rock', value='rock'),
        app_commands.Choice(name='Paper', value='paper'),
        app_commands.Choice(name='Scissors', value='scissors')
    ])
    async def rps(self, ctx, choice: str):
        """Play rock-paper-scissors with the bot"""
        choice = choice.lower()
        opts = ['rock', 'paper', 'scissors']
        emojis = {'rock': '🤜', 'paper': '🤚', 'scissors': '✌️'}
        
        if choice not in opts:
            await ctx.send('Choose rock, paper, or scissors')
            return
            
        bot_choice = random.choice(opts)
        result = 'draw'
        score = 0
        
        if (choice == 'rock' and bot_choice == 'scissors') or \
           (choice == 'scissors' and bot_choice == 'paper') or \
           (choice == 'paper' and bot_choice == 'rock'):
            result = 'win'
            score = 100
        elif choice != bot_choice:
            result = 'lose'
            score = 25
        else:
            score = 50
            
        embed = discord.Embed(
            title="Rock Paper Scissors",
            description=f"You played {emojis[choice]} vs Bot's {emojis[bot_choice]}",
            color=discord.Color.blue() if result == 'win' else 
                  discord.Color.gold() if result == 'draw' else 
                  discord.Color.red()
        )
        
        result_messages = {
            'win': '🎉 You win!',
            'lose': '😢 You lose!',
            'draw': '🤝 It\'s a draw!'
        }
        
        embed.add_field(name="Result", value=result_messages[result], inline=False)
        await ctx.send(embed=embed)
        
        await self.update_score(ctx.author.id, 'rps', score)
        
    @commands.hybrid_command(name='connect4', description='Play Connect 4 game')
    async def connect4(self, ctx):
        """Play Connect 4 against the bot"""
        WIDTH = 7
        HEIGHT = 6
        board = [[' ' for _ in range(WIDTH)] for _ in range(HEIGHT)]
        
        def format_board():
            nums = ' '.join(str(i+1) for i in range(WIDTH))
            rows = ['\n'.join('|' + ''.join(row) + '|' for row in board)]
            return f'```\n{nums}\n{"-"*(WIDTH+2)}\n{"".join(rows)}\n{"-"*(WIDTH+2)}```'
            
        def can_place(col):
            return board[0][col] == ' '
            
        def place_piece(col, piece):
            for row in range(HEIGHT-1, -1, -1):
                if board[row][col] == ' ':
                    board[row][col] = piece
                    return row
            return -1
            
        def check_winner(row, col, piece):
            # Check horizontal
            for c in range(max(0, col-3), min(col+1, WIDTH-3)):
                if all(board[row][c+i] == piece for i in range(4)):
                    return True
                    
            # Check vertical
            if row <= HEIGHT-4 and all(board[row+i][col] == piece for i in range(4)):
                return True
                
            # Check diagonals
            for r, c in [(row-i, col-i) for i in range(4)]:
                if 0 <= r <= HEIGHT-4 and 0 <= c <= WIDTH-4:
                    if all(board[r+i][c+i] == piece for i in range(4)):
                        return True
                        
            for r, c in [(row-i, col+i) for i in range(4)]:
                if 0 <= r <= HEIGHT-4 and 0 <= c >= 3:
                    if all(board[r+i][c-i] == piece for i in range(4)):
                        return True
            return False
            
        # Game loop
        msg = await ctx.send(f"Connect 4\nYour move (1-7):{format_board()}")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
            
        while True:
            try:
                response = await self.bot.wait_for('message', check=check, timeout=30)
                try:
                    col = int(response.content) - 1
                    if not (0 <= col < WIDTH):
                        await ctx.send("Please choose a column between 1 and 7")
                        continue
                    if not can_place(col):
                        await ctx.send("That column is full!")
                        continue
                except ValueError:
                    await ctx.send("Please enter a number between 1 and 7")
                    continue
                    
                # Player move
                row = place_piece(col, 'X')
                if check_winner(row, col, 'X'):
                    await msg.edit(content=f"You win!{format_board()}")
                    await self.update_score(ctx.author.id, 'connect4', 100)
                    return
                    
                # Bot move
                valid_moves = [c for c in range(WIDTH) if can_place(c)]
                if not valid_moves:
                    await msg.edit(content=f"It's a draw!{format_board()}")
                    await self.update_score(ctx.author.id, 'connect4', 50)
                    return
                    
                bot_col = random.choice(valid_moves)
                bot_row = place_piece(bot_col, 'O')
                
                await msg.edit(content=f"Your move (1-7):{format_board()}")
                
                if check_winner(bot_row, bot_col, 'O'):
                    await msg.edit(content=f"Bot wins!{format_board()}")
                    await self.update_score(ctx.author.id, 'connect4', 25)
                    return
                    
            except asyncio.TimeoutError:
                await ctx.send("Game timed out!")
                return
        choice = choice.lower()
        opts = ['rock', 'paper', 'scissors']
        if choice not in opts:
            await ctx.send('Choose rock, paper, or scissors')
            return


    @commands.command(name='guess', description='Guess the number between 1 and 100')
    async def guess(self, ctx):
        number = random.randint(1, 100)
        await ctx.send('I have chosen a number between 1 and 100. Send guesses in chat. You have 10 attempts.')
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        attempts = 10
        for i in range(attempts):
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30)
                val = int(msg.content.strip())
                if val == number:
                    await ctx.send(f'Correct! You took {i+1} attempts.')
                    return
                elif val < number:
                    await ctx.send('Higher')
                else:
                    await ctx.send('Lower')
            except asyncio.TimeoutError:
                await ctx.send('Timed out. Game over.')
                return
            except ValueError:
                await ctx.send('Send only numbers')
        await ctx.send(f'Out of attempts. The number was {number}.')

    @app_commands.command(name='guess', description='Play guess-the-number (starts a session in channel)')
    async def slash_guess(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channel = interaction.channel
        user = interaction.user
        number = random.randint(1, 100)
        await channel.send(f'{user.mention} I have chosen a number between 1 and 100. Send guesses in chat. You have 10 attempts.')
        def check(m):
            return m.author.id == user.id and m.channel.id == channel.id
        attempts = 10
        for i in range(attempts):
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30)
                val = int(msg.content.strip())
                if val == number:
                    await channel.send(f'Correct! You took {i+1} attempts.')
                    return
                elif val < number:
                    await channel.send('Higher')
                else:
                    await channel.send('Lower')
            except asyncio.TimeoutError:
                await channel.send('Timed out. Game over.')
                return
            except ValueError:
                await channel.send('Send only numbers')
        await channel.send(f'Out of attempts. The number was {number}.')


async def setup(bot: commands.Bot):
    cog = Games(bot)
    await cog.cog_load()
    await bot.add_cog(cog)

