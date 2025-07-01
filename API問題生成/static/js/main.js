/**
 * 小学生向け問題生成学習サイト - 学年対応強化版JavaScript
 */

class QuestionApp {
    constructor(subject) {
        this.subject = subject;
        this.currentGrade = 1; // level → grade に変更
        this.currentQuestion = null;
        this.selectedAnswer = null;
        this.isGenerating = false;
        this.stats = {
            correct: 0,
            total: 0
        };
        this.generationHistory = [];
        this.streak = 0;

        this.initializeElements();
        this.bindEvents();
        this.loadStats();
        this.checkAPIStatus();
        this.updateGradeDisplay();
        this.loadNewQuestion();
    }

    /**
     * DOM要素を初期化
     */
    initializeElements() {
        this.questionArea = document.getElementById('question-area');
        this.resultArea = document.getElementById('result-area');
        this.newQuestionBtn = document.getElementById('new-question-btn');
        this.checkAnswerBtn = document.getElementById('check-answer-btn');
        this.gradeButtons = document.querySelectorAll('.grade-btn');

        // 統計表示要素
        this.correctCountEl = document.getElementById('correct-count');
        this.totalCountEl = document.getElementById('total-count');
        this.accuracyRateEl = document.getElementById('accuracy-rate');
        this.currentGradeStatEl = document.getElementById('current-grade-stat');

        // 学年表示要素（科目別idは動的に取得）
        this.currentGradeValueEl = document.getElementById('current-grade-value');

        // AI状態表示要素を追加
        this.createAIStatusElement();
    }

    /**
     * AI状態表示要素を作成
     */
    createAIStatusElement() {
        const header = document.querySelector('.header');
        this.aiStatusEl = document.createElement('div');
        this.aiStatusEl.className = 'ai-status';
        this.aiStatusEl.innerHTML = `
            <div class="ai-indicator">
                <span class="ai-icon">🤖</span>
                <span class="ai-text">AI状態確認中...</span>
            </div>
        `;
        header.appendChild(this.aiStatusEl);
    }

    /**
     * イベントリスナーを設定
     */
    bindEvents() {
        this.newQuestionBtn.addEventListener('click', () => {
            if (!this.isGenerating) {
                this.loadNewQuestion();
                this.playSound('click');
            }
        });

        this.checkAnswerBtn.addEventListener('click', () => {
            this.checkAnswer();
            this.playSound('submit');
        });

        // 学年ボタンのイベント
        this.gradeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (!this.isGenerating) {
                    const grade = parseInt(e.currentTarget.dataset.grade);
                    this.selectGrade(grade);
                    this.playSound('select');
                }
            });
        });

        // キーボードショートカット
        document.addEventListener('keydown', (e) => {
            if (this.isGenerating) return;

            if (e.key === 'Enter' && this.selectedAnswer !== null) {
                this.checkAnswer();
            } else if (e.key === ' ' || e.key === 'Spacebar') {
                e.preventDefault();
                this.loadNewQuestion();
            } else if (e.key >= '1' && e.key <= '4') {
                const index = parseInt(e.key) - 1;
                const choiceBtns = this.questionArea.querySelectorAll('.choice-btn');
                if (choiceBtns[index] && !choiceBtns[index].disabled) {
                    choiceBtns[index].click();
                }
            } else if (e.ctrlKey && e.key >= '1' && e.key <= '6') {
                // Ctrl + 数字で学年変更
                e.preventDefault();
                const grade = parseInt(e.key);
                this.selectGrade(grade);
            }
        });
    }

    /**
     * 学年を選択
     */
    selectGrade(grade) {
        if (grade < 1 || grade > 6) return;

        // 前の選択を解除
        this.gradeButtons.forEach(btn => btn.classList.remove('active'));

        // 新しい学年を選択
        const selectedBtn = document.querySelector(`[data-grade="${grade}"]`);
        if (selectedBtn) {
            selectedBtn.classList.add('active');
        }

        this.currentGrade = grade;
        this.updateGradeDisplay();
        this.loadStats(); // 学年別統計を読み込み
        this.updateStatsDisplay();

        // 新しい問題を読み込み
        if (!this.isGenerating) {
            this.loadNewQuestion();
        }

        // 学年変更をアニメーション
        this.animateGradeChange();
    }

    /**
     * 学年表示を更新
     */
    updateGradeDisplay() {
        const gradeText = `${this.currentGrade}年生`;

        if (this.currentGradeValueEl) {
            this.currentGradeValueEl.textContent = gradeText;
        }

        if (this.currentGradeStatEl) {
            this.currentGradeStatEl.textContent = gradeText;
        }

        // カリキュラム情報を更新（科目別idを使用）
        const curriculumEl = document.getElementById(`curriculum-info-${this.subject}`);
        if (curriculumEl && window.CURRICULUM_INFO) {
            const curriculumText = window.CURRICULUM_INFO[this.subject]?.[this.currentGrade] || '';
            curriculumEl.textContent = curriculumText;
        }

        // 学年詳細を更新
        this.updateGradeDetails();
    }

    /**
     * 学年詳細表示を更新
     */
    updateGradeDetails() {
        // data-grade属性を使用して学年別詳細を表示
        const gradeDetails = document.querySelectorAll('.grade-detail');
        gradeDetails.forEach((detail) => {
            const detailGrade = parseInt(detail.dataset.grade);
            if (detailGrade === this.currentGrade) {
                detail.style.display = 'block';
                detail.style.animation = 'fadeIn 0.5s ease';
            } else {
                detail.style.display = 'none';
            }
        });
    }

    /**
     * 学年変更アニメーション
     */
    animateGradeChange() {
        const gradeSelector = document.querySelector('.grade-selector');
        if (gradeSelector) {
            gradeSelector.style.transform = 'scale(1.05)';
            setTimeout(() => {
                gradeSelector.style.transform = 'scale(1)';
            }, 200);
        }
    }

    /**
     * API状態をチェック
     */
    async checkAPIStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            this.updateAIStatus(status);
        } catch (error) {
            console.error('API状態チェックエラー:', error);
            this.updateAIStatus({ gemini_configured: false, status: 'error' });
        }
    }

    /**
     * AI状態表示を更新
     */
    updateAIStatus(status) {
        const aiText = this.aiStatusEl.querySelector('.ai-text');
        const aiIcon = this.aiStatusEl.querySelector('.ai-icon');

        if (status.gemini_configured) {
            aiText.textContent = `Gemini AI問題生成 有効（1-6年生対応）`;
            aiIcon.textContent = '🤖';
            this.aiStatusEl.className = 'ai-status active';
        } else {
            aiText.textContent = 'フォールバック問題使用中（1-6年生対応）';
            aiIcon.textContent = '📚';
            this.aiStatusEl.className = 'ai-status fallback';
        }
    }

    /**
     * 統計データを読み込み（学年別）
     */
    loadStats() {
        const statsKey = `stats_${this.subject}_grade${this.currentGrade}`;
        const savedStats = localStorage.getItem(statsKey);
        if (savedStats) {
            this.stats = JSON.parse(savedStats);
        } else {
            this.stats = { correct: 0, total: 0 };
        }
        this.updateStatsDisplay();
    }

    /**
     * 統計データを保存（学年別）
     */
    saveStats() {
        const statsKey = `stats_${this.subject}_grade${this.currentGrade}`;
        localStorage.setItem(statsKey, JSON.stringify(this.stats));
    }

    /**
     * 統計表示を更新
     */
    updateStatsDisplay() {
        if (this.correctCountEl) {
            this.correctCountEl.textContent = this.stats.correct;
        }
        if (this.totalCountEl) {
            this.totalCountEl.textContent = this.stats.total;
        }
        if (this.accuracyRateEl) {
            const rate = this.stats.total > 0 ?
                Math.round((this.stats.correct / this.stats.total) * 100) : 0;
            this.accuracyRateEl.textContent = `${rate}%`;
        }
    }

    /**
     * 新しい問題を読み込み
     */
    async loadNewQuestion() {
        if (this.isGenerating) return;

        this.isGenerating = true;
        this.showGeneratingState();
        this.resetState();

        try {
            const startTime = Date.now();

            const response = await fetch('/api/generate_question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    subject: this.subject,
                    grade: this.currentGrade // level → grade に変更
                })
            });

            const data = await response.json();

            if (data.success) {
                this.currentQuestion = data.question;

                // 生成履歴を記録
                this.generationHistory.push({
                    timestamp: Date.now(),
                    subject: this.subject,
                    grade: this.currentGrade,
                    generationTime: data.generation_time,
                    generatedBy: data.generated_by
                });

                // 最低限の表示時間を確保
                const minDisplayTime = 1000;
                const elapsedTime = Date.now() - startTime;
                const remainingTime = Math.max(0, minDisplayTime - elapsedTime);

                await this.sleep(remainingTime);

                this.displayQuestion();
                this.showGenerationInfo(data);
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Error loading question:', error);
            this.showError('問題の読み込みに失敗しました。もう一度お試しください。');
        } finally {
            this.isGenerating = false;
        }
    }

    /**
     * 生成中の状態を表示
     */
    showGeneratingState() {
        this.newQuestionBtn.disabled = true;
        this.newQuestionBtn.innerHTML = `
            <span class="btn-icon">⏳</span>
            ${this.currentGrade}年生の問題を生成中...
        `;

        this.questionArea.innerHTML = `
            <div class="loading">
                <div class="ai-generating">
                    <div class="ai-brain">🧠</div>
                    <div class="generating-text">
                        ${this.currentGrade}年生レベルの問題をAIが考え中...
                    </div>
                    <div class="loading-dots">
                        <span>.</span><span>.</span><span>.</span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 生成情報を表示
     */
    showGenerationInfo(data) {
        if (data.generation_time && data.generated_by) {
            const info = document.createElement('div');
            info.className = 'generation-info';
            info.innerHTML = `
                <small>
                    ${data.generated_by === 'Gemini AI Enhanced' ? '🧠 Gemini AI生成' : '📚 内蔵問題'} 
                    (${data.generation_time}秒) - ${this.currentGrade}年生レベル
                </small>
            `;
            this.questionArea.appendChild(info);

            setTimeout(() => {
                if (info.parentNode) {
                    info.style.opacity = '0';
                    setTimeout(() => info.remove(), 300);
                }
            }, 3000);
        }
    }

    /**
     * 状態をリセット
     */
    resetState() {
        this.selectedAnswer = null;
        this.resultArea.innerHTML = '';
        this.checkAnswerBtn.style.display = 'none';

        setTimeout(() => {
            this.newQuestionBtn.disabled = false;
            this.newQuestionBtn.innerHTML = `
                <span class="btn-icon">🔄</span>
                新しい問題
            `;
        }, 100);
    }

    /**
     * エラー表示
     */
    showError(message) {
        this.questionArea.innerHTML = `
            <div class="loading">
                <p style="color: #dc3545;">❌ ${message}</p>
            </div>
        `;
    }

    /**
     * 問題を表示
     */
    displayQuestion() {
        const questionHtml = `
            <div class="question-container">
                <div class="question-header">
                    <span class="grade-badge">${this.currentGrade}年生</span>
                    <span class="subject-badge">${this.getSubjectName()}</span>
                </div>
                <div class="question">${this.currentQuestion.question}</div>
                <div class="choices">
                    ${this.currentQuestion.choices.map((choice, index) => `
                        <button class="choice-btn" data-index="${index}" aria-label="選択肢${index + 1}: ${choice}">
                            <span class="choice-number">${index + 1}</span>
                            <span class="choice-text">${choice}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
        `;

        this.questionArea.innerHTML = questionHtml;
        this.bindChoiceEvents();
        this.animateQuestionAppear();
    }

    /**
     * 科目名を取得
     */
    getSubjectName() {
        const subjectNames = { 'math': '算数', 'english': '英語', 'kanji': '漢字' };
        return subjectNames[this.subject] || this.subject;
    }

    /**
     * 選択肢のイベントを設定
     */
    bindChoiceEvents() {
        const choiceBtns = this.questionArea.querySelectorAll('.choice-btn');
        choiceBtns.forEach((btn, index) => {
            btn.addEventListener('click', (e) => {
                this.selectChoice(index);
                this.playSound('select');
            });

            btn.addEventListener('mouseenter', () => {
                this.playSound('hover');
            });
        });
    }

    /**
     * 選択肢を選択
     */
    selectChoice(index) {
        const choiceBtns = this.questionArea.querySelectorAll('.choice-btn');

        choiceBtns.forEach(btn => btn.classList.remove('selected'));
        choiceBtns[index].classList.add('selected');
        this.selectedAnswer = index;
        this.checkAnswerBtn.style.display = 'inline-block';

        choiceBtns[index].style.transform = 'scale(1.05)';
        setTimeout(() => {
            choiceBtns[index].style.transform = '';
        }, 200);
    }

    /**
     * 回答をチェック
     */
    async checkAnswer() {
        if (this.selectedAnswer === null) {
            this.showNotification('答えを選択してください。', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/check_answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    answer: this.selectedAnswer,
                    correct_answer: this.currentQuestion.correct_answer,
                    explanation: this.currentQuestion.explanation,
                    grade: this.currentGrade
                })
            });

            const result = await response.json();

            // 統計を更新
            this.stats.total++;
            if (result.correct) {
                this.stats.correct++;
            }
            this.saveStats();
            this.updateStatsDisplay();

            this.displayResult(result);
            this.highlightAnswers(result.correct);
            this.checkAnswerBtn.style.display = 'none';

            this.playSound(result.correct ? 'correct' : 'incorrect');
            this.checkStreak(result.correct);

        } catch (error) {
            console.error('Error checking answer:', error);
            this.showNotification('エラーが発生しました。', 'error');
        }
    }

    /**
     * 連続正解をチェック
     */
    checkStreak(isCorrect) {
        if (!this.streak) this.streak = 0;

        if (isCorrect) {
            this.streak++;
            if (this.streak >= 5) {
                this.showStreakCelebration(this.streak);
            }
        } else {
            this.streak = 0;
        }
    }

    /**
     * 連続正解のお祝い表示
     */
    showStreakCelebration(streak) {
        const gradeMessage = this.getGradeStreakMessage(streak);
        this.showNotification(gradeMessage, 'success');
        this.celebrateCorrectAnswer();
    }

    /**
     * 学年別連続正解メッセージ
     */
    getGradeStreakMessage(streak) {
        const messages = {
            1: `🌟 ${streak}もんれんぞくせいかい！すごいね！`,
            2: `✨ ${streak}問連続正解！とてもよくできました！`,
            3: `🎉 ${streak}問連続正解！すばらしいです！`,
            4: `🏆 ${streak}問連続正解！とても優秀です！`,
            5: `🔥 ${streak}問連続正解！素晴らしい集中力！`,
            6: `🌟 ${streak}問連続正解！完璧な理解力です！`
        };
        return messages[this.currentGrade] || messages[1];
    }

    /**
     * 結果を表示
     */
    displayResult(result) {
        const resultClass = result.correct ? 'correct' : 'incorrect';
        const icon = result.correct ? this.getCorrectIcon() : this.getIncorrectIcon();

        this.resultArea.innerHTML = `
            <div class="result ${resultClass}">
                <div class="result-header">
                    <span class="result-grade-badge">${this.currentGrade}年生レベル</span>
                </div>
                <div class="result-message">${icon} ${result.message}</div>
                <div class="result-explanation">
                    ${result.explanation}
                </div>
                ${this.streak >= 3 ? `<div class="streak-counter">連続正解: ${this.streak}問 🔥</div>` : ''}
            </div>
        `;

        if (result.correct) {
            this.celebrateCorrectAnswer();
        }
    }

    /**
     * 学年別正解アイコン
     */
    getCorrectIcon() {
        const icons = {
            1: '🌟', 2: '✨', 3: '🎉', 4: '🏆', 5: '💫', 6: '🌟'
        };
        return icons[this.currentGrade] || '🎉';
    }

    /**
     * 学年別不正解アイコン
     */
    getIncorrectIcon() {
        const icons = {
            1: '😊', 2: '😊', 3: '😊', 4: '😊', 5: '😊', 6: '😊'
        };
        return icons[this.currentGrade] || '😊';
    }

    /**
     * 正解時のお祝い効果
     */
    celebrateCorrectAnswer() {
        const celebration = document.createElement('div');
        celebration.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1000;
        `;

        const emojis = this.getGradeCelebrationEmojis();

        for (let i = 0; i < 15; i++) {
            setTimeout(() => {
                const emoji = document.createElement('div');
                emoji.textContent = emojis[Math.floor(Math.random() * emojis.length)];
                emoji.style.cssText = `
                    position: absolute;
                    font-size: ${1.5 + Math.random()}rem;
                    left: ${Math.random() * 100}%;
                    top: -50px;
                    animation: fall 3s ease-out forwards;
                    transform: rotate(${Math.random() * 360}deg);
                `;
                celebration.appendChild(emoji);

                setTimeout(() => emoji.remove(), 3000);
            }, i * 100);
        }

        document.body.appendChild(celebration);
        setTimeout(() => celebration.remove(), 3500);
    }

    /**
     * 学年別お祝い絵文字
     */
    getGradeCelebrationEmojis() {
        const emojiSets = {
            1: ['🌟', '⭐', '✨', '🎈', '🎀', '🦄'],
            2: ['🎉', '🎊', '✨', '🌟', '🏅', '🎯'],
            3: ['🏆', '🥇', '⭐', '💫', '🌟', '🎖️'],
            4: ['🔥', '💎', '🌟', '⚡', '🏆', '👑'],
            5: ['🚀', '💫', '⭐', '🌟', '🔥', '🎯'],
            6: ['👑', '💎', '🏆', '🌟', '⚡', '🔥']
        };
        return emojiSets[this.currentGrade] || emojiSets[1];
    }

    /**
     * 答えをハイライト
     */
    highlightAnswers(isCorrect) {
        const choiceBtns = this.questionArea.querySelectorAll('.choice-btn');
        choiceBtns.forEach((btn, index) => {
            btn.disabled = true;
            if (index === this.currentQuestion.correct_answer) {
                btn.classList.add('correct');
            } else if (index === this.selectedAnswer && !isCorrect) {
                btn.classList.add('incorrect');
            }
        });
    }

    /**
     * 問題表示のアニメーション
     */
    animateQuestionAppear() {
        const container = this.questionArea.querySelector('.question-container');
        container.style.opacity = '0';
        container.style.transform = 'translateY(20px)';

        setTimeout(() => {
            container.style.transition = 'all 0.5s ease';
            container.style.opacity = '1';
            container.style.transform = 'translateY(0)';
        }, 100);
    }

    /**
     * 通知表示
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 10px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            animation: slideInRight 0.3s ease;
            max-width: 300px;
        `;

        switch (type) {
            case 'warning':
                notification.style.background = '#ffc107';
                notification.style.color = '#333';
                break;
            case 'error':
                notification.style.background = '#dc3545';
                break;
            case 'success':
                notification.style.background = '#28a745';
                break;
            default:
                notification.style.background = '#17a2b8';
        }

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    /**
     * 音効果
     */
    playSound(type) {
        if (!this.audioContext) {
            try {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            } catch (e) {
                return;
            }
        }

        const frequencies = {
            click: 800,
            select: 600,
            submit: 400,
            correct: 523.25,
            incorrect: 293.66,
            hover: 1000
        };

        const frequency = frequencies[type] || 440;
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);

        oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
        oscillator.type = 'sine';

        gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.2);

        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + 0.2);
    }

    /**
     * 学年統計を表示
     */
    showGradeStats() {
        const allStats = {};
        for (let grade = 1; grade <= 6; grade++) {
            const statsKey = `stats_${this.subject}_grade${grade}`;
            const stats = localStorage.getItem(statsKey);
            if (stats) {
                allStats[grade] = JSON.parse(stats);
            }
        }
        console.log('学年別統計:', allStats);
        return allStats;
    }

    /**
     * 全学年の統計をリセット
     */
    resetAllStats() {
        for (let grade = 1; grade <= 6; grade++) {
            const statsKey = `stats_${this.subject}_grade${grade}`;
            localStorage.removeItem(statsKey);
        }
        this.stats = { correct: 0, total: 0 };
        this.updateStatsDisplay();
        this.showNotification('全ての統計をリセットしました', 'info');
    }

    /**
     * 学習進捗を取得
     */
    getLearningProgress() {
        const allStats = this.showGradeStats();
        const progress = {};

        for (let grade = 1; grade <= 6; grade++) {
            const stats = allStats[grade] || { correct: 0, total: 0 };
            const rate = stats.total > 0 ? Math.round((stats.correct / stats.total) * 100) : 0;
            progress[grade] = {
                correctCount: stats.correct,
                totalCount: stats.total,
                accuracyRate: rate,
                isActive: grade === this.currentGrade
            };
        }

        return progress;
    }

    /**
     * 待機関数
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * デバッグ情報を表示
     */
    showDebugInfo() {
        console.log('=== デバッグ情報 ===');
        console.log('現在の科目:', this.subject);
        console.log('現在の学年:', this.currentGrade);
        console.log('現在の統計:', this.stats);
        console.log('連続正解数:', this.streak);
        console.log('生成履歴:', this.generationHistory);
        console.log('学習進捗:', this.getLearningProgress());
    }
}

// CSS アニメーションを動的に追加
if (!document.querySelector('#dynamic-animations-grade')) {
    const style = document.createElement('style');
    style.id = 'dynamic-animations-grade';
    style.textContent = `
        @keyframes fall {
            to {
                transform: translateY(100vh) rotate(720deg);
                opacity: 0;
            }
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        @keyframes loadingDots {
            0%, 20% { opacity: 0; }
            50% { opacity: 1; }
            100% { opacity: 0; }
        }
        
        @keyframes brainPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .ai-generating {
            text-align: center;
            padding: 40px;
        }
        
        .ai-brain {
            font-size: 3rem;
            animation: brainPulse 2s infinite;
            margin-bottom: 20px;
        }
        
        .generating-text {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 15px;
        }
        
        .loading-dots span {
            animation: loadingDots 1.5s infinite;
        }
        
        .loading-dots span:nth-child(2) {
            animation-delay: 0.3s;
        }
        
        .loading-dots span:nth-child(3) {
            animation-delay: 0.6s;
        }
        
        .ai-status {
            margin: 15px 0;
            padding: 12px 20px;
            border-radius: 25px;
            text-align: center;
            font-size: 0.9rem;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .ai-status.active {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
        }
        
        .ai-status.fallback {
            background: linear-gradient(45deg, #ffc107, #fd7e14);
            color: #333;
        }
        
        .ai-indicator {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .generation-info {
            text-align: center;
            margin-top: 15px;
            opacity: 0.7;
            transition: opacity 0.3s ease;
        }
        
        .choice-number {
            display: inline-block;
            width: 28px;
            height: 28px;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 50%;
            line-height: 28px;
            margin-right: 12px;
            font-size: 0.9rem;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .choice-btn.selected .choice-number {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.1);
        }
        
        .choice-btn.correct .choice-number {
            background: rgba(255, 255, 255, 0.4);
        }
        
        .choice-btn.incorrect .choice-number {
            background: rgba(255, 255, 255, 0.4);
        }
        
        .result-message {
            font-size: 1.4rem;
            margin-bottom: 15px;
        }
        
        .result-explanation {
            font-size: 1.1rem;
            font-weight: normal;
            line-height: 1.4;
        }
        
        .streak-counter {
            margin-top: 10px;
            font-size: 1rem;
            background: rgba(255, 165, 0, 0.2);
            padding: 8px 15px;
            border-radius: 20px;
            display: inline-block;
        }
        
        /* レスポンシブ対応 */
        @media (max-width: 768px) {
            .ai-generating {
                padding: 30px 20px;
            }
            
            .ai-brain {
                font-size: 2.5rem;
            }
            
            .generating-text {
                font-size: 1.1rem;
            }
            
            .choice-number {
                width: 24px;
                height: 24px;
                line-height: 24px;
                margin-right: 10px;
                font-size: 0.8rem;
            }
            
            .result-message {
                font-size: 1.2rem;
            }
            
            .result-explanation {
                font-size: 1rem;
            }
        }

        @media (max-width: 480px) {
            .ai-generating {
                padding: 25px 15px;
            }
            
            .ai-brain {
                font-size: 2rem;
            }
            
            .generating-text {
                font-size: 1rem;
            }
            
            .choice-number {
                width: 22px;
                height: 22px;
                line-height: 22px;
                margin-right: 8px;
                font-size: 0.7rem;
            }
            
            .result-message {
                font-size: 1.1rem;
            }
            
            .result-explanation {
                font-size: 0.9rem;
            }
            
            .streak-counter {
                font-size: 0.9rem;
                padding: 6px 12px;
            }
        }
    `;
    document.head.appendChild(style);
}

// グローバルに公開（テンプレートから使用するため）
window.QuestionApp = QuestionApp;

// デバッグ用のグローバル関数も追加
window.showDebugInfo = function() {
    if (window.questionAppInstance) {
        window.questionAppInstance.showDebugInfo();
    }
};

window.resetAllStats = function() {
    if (window.questionAppInstance) {
        window.questionAppInstance.resetAllStats();
    }
};

window.showAllGradeStats = function() {
    if (window.questionAppInstance) {
        return window.questionAppInstance.showGradeStats();
    }
};

// アプリケーションインスタンスをグローバルに保存
document.addEventListener('DOMContentLoaded', () => {
    if (typeof SUBJECT !== 'undefined') {
        window.questionAppInstance = new QuestionApp(SUBJECT);
    }
});