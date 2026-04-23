import { useState, useEffect, useRef } from "react";
import { createExpense, listExpenses } from "./api";
import type { Expense, ExpenseCreate } from "./api";
import "./App.css";

// ─── ExpenseForm ─────────────────────────────────────────────────────────────

interface FormState {
  amount: string;
  category: string;
  description: string;
  date: string;
}

const EMPTY_FORM: FormState = { amount: "", category: "", description: "", date: "" };

interface ExpenseFormProps {
  onCreated: (expense: Expense) => void;
}

function ExpenseForm({ onCreated }: ExpenseFormProps) {
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const idempotencyKeyRef = useRef<string | null>(null);

  function newKey() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
    });
  }

  async function submit(e?: React.FormEvent | React.MouseEvent) {
    e?.preventDefault();
    if (!idempotencyKeyRef.current) {
      idempotencyKeyRef.current = newKey();
    }
    setSubmitting(true);
    setError(null);
    try {
      const payload: ExpenseCreate = {
        amount: form.amount,
        category: form.category.trim(),
        description: form.description.trim(),
        date: form.date,
      };
      const expense = await createExpense(payload, idempotencyKeyRef.current);
      idempotencyKeyRef.current = null;
      setForm(EMPTY_FORM);
      onCreated(expense);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unexpected error. Please retry.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="expense-form" onSubmit={submit}>
      <h2>Add Expense</h2>
      {error && (
        <div className="form-error" role="alert">
          <span>{error}</span>
          <button type="button" className="retry-btn" onClick={submit}>
            Retry
          </button>
        </div>
      )}
      <div className="form-row">
        <label>
          Amount (₹)
          <input
            type="number"
            step="0.01"
            min="0.01"
            required
            value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })}
            placeholder="0.00"
          />
        </label>
        <label>
          Category
          <input
            type="text"
            required
            maxLength={50}
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
            placeholder="Food, Transport…"
          />
        </label>
      </div>
      <div className="form-row">
        <label>
          Date
          <input
            type="date"
            required
            value={form.date}
            onChange={(e) => setForm({ ...form, date: e.target.value })}
          />
        </label>
        <label>
          Description
          <input
            type="text"
            maxLength={500}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Optional note"
          />
        </label>
      </div>
      <button type="submit" disabled={submitting} className="submit-btn">
        {submitting ? "Saving…" : "Add Expense"}
      </button>
    </form>
  );
}

// ─── FilterBar ────────────────────────────────────────────────────────────────

interface FilterBarProps {
  category: string;
  sort: string;
  categories: string[];
  onChange: (category: string, sort: string) => void;
}

function FilterBar({ category, sort, categories, onChange }: FilterBarProps) {
  return (
    <div className="filter-bar">
      <label>
        Category&nbsp;
        <select value={category} onChange={(e) => onChange(e.target.value, sort)}>
          <option value="">All</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </label>
      <label>
        Sort&nbsp;
        <select value={sort} onChange={(e) => onChange(category, e.target.value)}>
          <option value="date_desc">Date ↓ (newest)</option>
          <option value="date_asc">Date ↑ (oldest)</option>
        </select>
      </label>
    </div>
  );
}

// ─── TotalDisplay ─────────────────────────────────────────────────────────────

function TotalDisplay({ expenses }: { expenses: Expense[] }) {
  const total = expenses.reduce((sum, e) => sum + Math.round(parseFloat(e.amount) * 100), 0);
  return (
    <div className="total-display">
      Total: <strong>₹{(total / 100).toFixed(2)}</strong>
    </div>
  );
}

// ─── ExpenseList ──────────────────────────────────────────────────────────────

interface ExpenseListProps {
  expenses: Expense[];
  loading: boolean;
  error: string | null;
}

function ExpenseList({ expenses, loading, error }: ExpenseListProps) {
  if (loading) return <p className="state-msg">Loading…</p>;
  if (error) return <p className="state-msg error">{error}</p>;
  if (expenses.length === 0) return <p className="state-msg">No expenses yet. Add one above.</p>;

  return (
    <table className="expense-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Category</th>
          <th>Description</th>
          <th>Amount (₹)</th>
        </tr>
      </thead>
      <tbody>
        {expenses.map((e) => (
          <tr key={e.id}>
            <td>{e.date}</td>
            <td>{e.category}</td>
            <td>{e.description || "—"}</td>
            <td className="amount-cell">{parseFloat(e.amount).toFixed(2)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [category, setCategory] = useState("");
  const [sort, setSort] = useState("date_desc");

  const allCategories = Array.from(new Set(expenses.map((e) => e.category))).sort();
  const visible = category ? expenses.filter((e) => e.category === category) : expenses;

  async function fetchExpenses(cat: string, s: string) {
    setLoading(true);
    setListError(null);
    try {
      const data = await listExpenses({ category: cat || undefined, sort: s });
      setExpenses(data);
    } catch {
      setListError("Failed to load expenses. Please refresh.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchExpenses(category, sort);
  }, [category, sort]);

  function handleCreated(expense: Expense) {
    setExpenses((prev) => {
      const updated = [expense, ...prev.filter((e) => e.id !== expense.id)];
      if (sort === "date_desc") {
        updated.sort((a, b) => b.date.localeCompare(a.date) || b.id - a.id);
      } else {
        updated.sort((a, b) => a.date.localeCompare(b.date) || a.id - b.id);
      }
      return updated;
    });
  }

  function handleFilterChange(cat: string, s: string) {
    setCategory(cat);
    setSort(s);
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Expense Tracker</h1>
      </header>
      <main className="app-main">
        <ExpenseForm onCreated={handleCreated} />
        <section className="list-section">
          <div className="list-header">
            <FilterBar
              category={category}
              sort={sort}
              categories={allCategories}
              onChange={handleFilterChange}
            />
            <TotalDisplay expenses={visible} />
          </div>
          <ExpenseList expenses={visible} loading={loading} error={listError} />
        </section>
      </main>
    </div>
  );
}
