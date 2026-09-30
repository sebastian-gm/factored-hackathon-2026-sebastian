import type { Config, Transaction } from "../contracts";
export const BANK_CLOCK = "2026-06-18T06:00:00Z";
export const DATASET = "frontend-fixtures-v1";
export const personas: Config["personas"] = [
  {
    username: "demo.es.mx",
    label: "México · cargo pendiente",
    role: "customer",
    locale: "es-MX",
  },
  {
    username: "demo.es.co",
    label: "Colombia · revisión de compra",
    role: "customer",
    locale: "es-CO",
  },
  {
    username: "demo.es.ar",
    label: "Argentina · revisión de compra",
    role: "customer",
    locale: "es-AR",
  },
  {
    username: "demo.pt.br",
    label: "México · conversación en portugués",
    role: "customer",
    locale: "pt-BR",
  },
  {
    username: "demo.fraud",
    label: "México · atención de fraude",
    role: "customer",
    locale: "es-MX",
  },
  {
    username: "demo.agent",
    label: "Agent Desk · atención humana",
    role: "agent",
    locale: "es-MX",
  },
  {
    username: "demo.ops",
    label: "Ops · supervisión",
    role: "ops",
    locale: "es-MX",
  },
];
// Entirely invented records. Never copy organizer records into this module.
export const transactions: Transaction[] = [
  {
    handle: "txn_cafe",
    merchant: "Café Horizonte",
    amount: 185,
    currency: "USD",
    transaction_date: "2026-06-16T12:00:00Z",
    transaction_type: "Purchase",
    status: "Pending",
  },
  {
    handle: "txn_livraria",
    merchant: "Livraria Aurora",
    amount: 89.9,
    currency: "USD",
    transaction_date: "2026-06-14T12:00:00Z",
    transaction_type: "Purchase",
    status: "Approved",
  },
  {
    handle: "txn_mercado",
    merchant: "Mercado do Bairro",
    amount: 92.5,
    currency: "USD",
    transaction_date: "2026-06-14T15:00:00Z",
    transaction_type: "Purchase",
    status: "Approved",
  },
  {
    handle: "txn_estudio",
    merchant: "Estúdio Verde",
    amount: 88,
    currency: "USD",
    transaction_date: "2026-06-15T12:00:00Z",
    transaction_type: "Purchase",
    status: "Approved",
  },
];

export function transactionsForPersona(username: string): Transaction[] {
  // Country is part of the authored persona, independent of conversation locale.
  // The legacy demo.pt.br alias is a Portuguese speaker in Mexico, not Brazil.
  const currency =
    username === "demo.es.co"
      ? "COP"
      : username === "demo.es.ar"
        ? "ARS"
        : "USD";
  return transactions.map((transaction) => ({ ...transaction, currency }));
}
