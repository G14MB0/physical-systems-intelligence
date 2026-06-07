import type { WorkflowUiResult } from "../services/api";

export function ActionTicketPanel({ result }: { result: WorkflowUiResult }) {
  if (!result.ticket) {
    return null;
  }

  return (
    <div className="ticket">
      <strong>Ticket PSI-{result.ticket.id}</strong>
      <span>{result.ticket.title}</span>
    </div>
  );
}
