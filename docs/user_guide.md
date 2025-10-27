# 🧭 ExpenseVista User Guide

Welcome to **ExpenseVista** — your smart personal finance companion.  
This guide walks you through everything you need to know to make the most of your budgets, expenses, incomes, and AI assistant.

---

## 🪄 What Is ExpenseVista?

**ExpenseVista** helps you take control of your finances.  
You can:
- Create and manage budgets by category (e.g. groceries, rent, utilities)
- Track your daily expenses and incomes
- Receive email alerts when spending approaches or exceeds your budget
- Ask the built-in **AI Assistant** natural questions like:
  > “How much did I spend this week?”  
  > “Am I over budget on transport this month?”  
  > “What’s my top category this quarter?”

Whether you’re an individual, freelancer, or household manager — ExpenseVista helps you stay on track financially.

---

## 🔐 Getting Started

### 1️⃣ Sign Up or Log In

1. Go to your ExpenseVista web app URL (expensevista.com).  
2. Click **Sign Up** if you’re new, or **Log In** if you already have an account.  
3. You’ll receive a verification link or welcome email.  

Your account uses **secure JWT authentication**, keeping your data private and safe.

---

## 🏠 Dashboard Overview

After logging in, you’ll see your **Financial Dashboard**, which includes:

- 💰 **Total Income**
- 💸 **Total Expenses**
- 💹 **Net Balance (Income – Expenses)**
- 📊 **Charts by category and time period**
- 🧾 **Quick actions** to add new expenses, incomes, or budgets

The dashboard provides a snapshot of your current financial health and trends over time.

---

## 🎯 Managing Budgets

Budgets are at the heart of ExpenseVista. You can plan how much you want to spend per category and time period.

### ➕ Create a New Budget
1. Navigate to **Budgets** in the sidebar.
2. Click **Add Budget**.
3. Fill out:
   - **Category** (e.g. groceries, utilities, travel)
   - **Limit amount**
   - **Period** (weekly, monthly, quarterly, yearly)
4. Click **Save**.

Your budget will appear in the list, with tracking progress automatically updated as you log expenses.

### ✏️ Edit or Delete Budgets
- To edit, click the **Edit** button next to an existing budget.
- To delete, click the **Trash** icon.

### ✉️ Automatic Alerts
ExpenseVista automatically monitors your budgets:
- 50% → **“You’ve used half your budget.”**
- 80–99% → **“You’re nearing your limit.”**
- 100%+ → **“You’ve exceeded your budget.”**

You’ll receive email notifications powered by **AWS SES**, ensuring reliable delivery.

---

## 🧾 Adding and Tracking Expenses

### ➕ Add an Expense
1. Go to the **Expenses** page.
2. Click **Add Expense**.
3. Enter:
   - **Category** (match or create one)
   - **Amount**
   - **Date**
   - Optional **Note**
4. Click **Save Expense**.

Expenses automatically count toward your active budgets.

### 📊 View Expenses
- Use the **filters** to view expenses by date range or category.
- Sort to see which areas consume most of your spending.

---

## 💰 Recording Income

Track where your money comes from — whether it’s your job, freelance work, or investments.

### ➕ Add Income
1. Go to **Income**.
2. Click **Add Income**.
3. Fill in:
   - **Source** (e.g. salary, freelance, dividends)
   - **Amount**
   - **Date received**
   - **Category** (active or passive)
4. Save your entry.

### 📈 Analyze Income
You can view total and categorized incomes by week, month, quarter, or year.

---

## ✉️ Email Notifications

You’ll automatically receive well-formatted HTML email alerts when:
- Your spending hits key thresholds (50%, 80%, 100%)
- You exceed a budget category limit

Each email includes:
- Your username
- Category name
- Budget period
- Personalized message

> Example:  
> “Hi Andrew, your transport budget for this month is almost used up. You’ve spent €180 out of €200.”

All emails are securely delivered through **AWS Simple Email Service (SES)**.

---

## 📊 Financial Overview & Reports

Navigate to the **Summary** page for a high-level view of your finances.

You’ll see:
- Income vs Expense charts
- Category breakdowns
- Net savings or deficit
- Filters for weekly, monthly, quarterly, and yearly views

ExpenseVista keeps your data organized so you can spot spending patterns quickly.

---

## 🤖 Using the AI Assistant

The built-in AI Assistant helps you query your data conversationally.

### 💬 Example Questions You Can Ask

**Spending**
- “How much did I spend this week?”
- “How much did I spend on groceries last month?”
- “Spending between June and August?”

**Budgets**
- “Am I over budget on transport this month?”
- “What’s my highest budget this year?”
- “What’s my lowest budget this quarter?”
- “Total budget for this month?”

**Income**
- “What’s my income this year?”
- “Compare my income vs expenses this month.”
- “What’s my savings in the last 20 days?”

### 💡 Tips for Best Results
- Be specific: include **time periods** like “this month” or “last year”.
- Mention categories when possible (e.g. “groceries”, “transport”).
- Avoid ambiguous words like “recently” — try “in the last 30 days” instead.

### 🧩 How It Works
- The assistant uses both AI (OpenAI model) and a **rules-based interpreter**.
- If the AI misses context, the fallback ensures accurate results for known patterns.
- You’ll always receive a clear, humanized reply — no confusing JSON or technical output.

---

## 💡 FAQ

### ❓ Why do my totals look different from my bank account?
ExpenseVista only tracks entries you log. If some expenses or incomes aren’t entered, they won’t appear in reports.

### ❓ Can I track multiple accounts?
Currently, ExpenseVista focuses on personal finance. Future versions may allow linking multiple accounts.

### ❓ How do I reset my password?
Use the **Forgot Password** option on the login page. You’ll receive an email with reset instructions.

### ❓ I didn’t receive an alert email.
Check your spam or promotions folder. Ensure your email is verified in your profile settings.

### ❓ What happens if I delete a budget?
Deleting a budget removes only the budget entry — your expenses and incomes remain intact.

---

## 🛠️ Troubleshooting

| Issue | Possible Fix |
|--------|---------------|
| **AI Assistant doesn’t respond** | Try rephrasing your question or specify a period like “this month”. |
| **Emails not sending** | Check your `.env` AWS SES credentials and region configuration. |
| **Data not saving** | Make sure your PostgreSQL database is running and migrations are up-to-date. |
| **Dates look off** | Ensure your system timezone matches the UTC timestamps ExpenseVista uses internally. |

---

## 🌱 Tips for Smart Budgeting

- Set **realistic limits** based on past spending.  
- Review your **top categories** monthly to adjust budgets.  
- Use **quarterly or yearly** budgets for long-term planning.  
- Ask the assistant:  
  > “What’s my top category this quarter?”  
  to understand where you spend most.

---

## 🧭 Summary

ExpenseVista empowers you to:
- Plan budgets by category and period  
- Track spending and income  
- Receive smart alerts and reports  
- Use natural language to understand your finances  

It’s your personal finance hub — clear, actionable, and intelligent.

---

## 💬 Support

If you encounter any issues or have suggestions:  
📧 **Email:** support@expensevista.com  
🐙 **GitHub Issues:** [github.com/Andrew-O39/expense_vista/issues](https://github.com/Andrew-O39/expense_vista/issues)

---

© 2025 **ExpenseVista** — Personal Finance Simplified 💰