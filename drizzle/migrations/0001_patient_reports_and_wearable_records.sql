CREATE TABLE public.patient_reports (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 patient_id uuid NOT NULL,
 filename text NOT NULL,
 storage_path text NOT NULL,
 document_patient text NOT NULL DEFAULT '',
 collected_on date NOT NULL,
 laboratory text NOT NULL DEFAULT '',
 exams jsonb NOT NULL DEFAULT '[]'::jsonb,
 created_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, DELETE ON public.patient_reports TO authenticated;
GRANT ALL ON public.patient_reports TO service_role;
ALTER TABLE public.patient_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY reports_owner_read ON public.patient_reports FOR SELECT TO authenticated USING (patient_id = auth.uid() AND public.has_role(auth.uid(), 'patient'));
CREATE POLICY reports_owner_insert ON public.patient_reports FOR INSERT TO authenticated WITH CHECK (patient_id = auth.uid() AND public.has_role(auth.uid(), 'patient') AND storage_path = auth.uid()::text || '/' || id::text || '.pdf');
CREATE POLICY reports_owner_delete ON public.patient_reports FOR DELETE TO authenticated USING (patient_id = auth.uid() AND public.has_role(auth.uid(), 'patient'));
CREATE INDEX patient_reports_history ON public.patient_reports(patient_id, collected_on);
CREATE TABLE public.patient_wearable_records (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 patient_id uuid NOT NULL,
 measured_on date NOT NULL,
 source text NOT NULL,
 metrics jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(patient_id, measured_on, source)
);
GRANT SELECT, INSERT, UPDATE, DELETE ON public.patient_wearable_records TO authenticated;
GRANT ALL ON public.patient_wearable_records TO service_role;
ALTER TABLE public.patient_wearable_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY wearable_owner_read ON public.patient_wearable_records FOR SELECT TO authenticated USING (patient_id = auth.uid() AND public.has_role(auth.uid(), 'patient'));
CREATE POLICY wearable_owner_insert ON public.patient_wearable_records FOR INSERT TO authenticated WITH CHECK (patient_id = auth.uid() AND public.has_role(auth.uid(), 'patient'));
CREATE POLICY wearable_owner_update ON public.patient_wearable_records FOR UPDATE TO authenticated USING (patient_id = auth.uid() AND public.has_role(auth.uid(), 'patient')) WITH CHECK (patient_id = auth.uid() AND public.has_role(auth.uid(), 'patient'));
CREATE POLICY wearable_owner_delete ON public.patient_wearable_records FOR DELETE TO authenticated USING (patient_id = auth.uid() AND public.has_role(auth.uid(), 'patient'));
CREATE POLICY patient_pdf_read ON storage.objects FOR SELECT TO authenticated USING (bucket_id = 'patient-reports' AND (storage.foldername(name))[1] = auth.uid()::text AND public.has_role(auth.uid(), 'patient'));
CREATE POLICY patient_pdf_insert ON storage.objects FOR INSERT TO authenticated WITH CHECK (bucket_id = 'patient-reports' AND (storage.foldername(name))[1] = auth.uid()::text AND public.has_role(auth.uid(), 'patient'));
CREATE POLICY patient_pdf_delete ON storage.objects FOR DELETE TO authenticated USING (bucket_id = 'patient-reports' AND (storage.foldername(name))[1] = auth.uid()::text AND public.has_role(auth.uid(), 'patient'));