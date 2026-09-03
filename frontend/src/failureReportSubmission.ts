export type FailureReportPayload = {
  category: string;
  summary: string;
  expected_behavior: string | null;
  evaluation_case_id: string | null;
};

type ResettableForm = Pick<HTMLFormElement, "reset">;
type InFlightFlag = { current: boolean };

export async function submitFailureReport({
  form,
  payload,
  inFlight,
  createReport,
}: {
  form: ResettableForm;
  payload: FailureReportPayload;
  inFlight: InFlightFlag;
  createReport: (payload: FailureReportPayload) => Promise<unknown>;
}): Promise<boolean> {
  if (inFlight.current) return false;

  inFlight.current = true;
  try {
    await createReport(payload);
    form.reset();
    return true;
  } finally {
    inFlight.current = false;
  }
}
