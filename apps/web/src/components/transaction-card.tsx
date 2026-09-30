"use client";
import { CreditCard, ArrowUpRight } from "lucide-react";
import { useTranslations } from "next-intl";
import type { Transaction } from "@/lib/contracts";
import { date, money } from "@/lib/format";
import { useApp } from "./workspace";
import { Button } from "./ui/button";
export function TransactionCard({
  transaction,
  onChoose,
  disabled,
}: {
  transaction: Transaction;
  onChoose?: () => void;
  disabled?: boolean;
}) {
  const t = useTranslations();
  const { locale, config } = useApp();
  const statuses: Record<string, string> = {
    Pending: "pending",
    Approved: "approved",
    Declined: "declined",
    Reversed: "reversed",
  };
  return (
    <article className="transaction-card">
      <div className="transaction-top">
        <span className="merchant-icon">
          <CreditCard size={20} />
        </span>
        <div>
          <h3>{transaction.merchant ?? t("merchantMissing")}</h3>
          <p>{config.fixtures ? t("demoProduct") : t("productMissing")}</p>
        </div>
        <ArrowUpRight size={17} className="muted" />
      </div>
      <div className="transaction-money">
        {money(transaction.amount, transaction.currency, locale)}
      </div>
      <div className="transaction-bottom">
        <time dateTime={transaction.transaction_date}>
          {date(transaction.transaction_date, locale)}
        </time>
        <span
          className={`badge ${transaction.status === "Pending" ? "amber" : ""}`}
        >
          {statuses[transaction.status]
            ? t(statuses[transaction.status])
            : t("statusUnknown")}
        </span>
      </div>
      {onChoose && (
        <Button
          variant="secondary"
          size="small"
          disabled={disabled}
          onClick={onChoose}
        >
          {t("selectCharge")}
          <ArrowUpRight size={15} />
        </Button>
      )}
    </article>
  );
}
