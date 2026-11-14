CREATE TABLE public.consultation_slots (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 doctor_id uuid NOT NULL REFERENCES public.profiles(id),
 starts_at timestamptz NOT NULL,
 ends_at timestamptz NOT NULL,
 modality text NOT NULL DEFAULT 'presencial' CHECK (modality IN ('presencial','online')),
 location text NOT NULL DEFAULT '' CHECK (length(location) <= 500),
 patient_id uuid REFERENCES public.profiles(id),
 booked_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(),
 CHECK (ends_at > starts_at),
 CHECK ((patient_id IS NULL AND booked_at IS NULL) OR (patient_id IS NOT NULL AND booked_at IS NOT NULL)),
 UNIQUE (doctor_id, starts_at)
);
GRANT SELECT, INSERT, DELETE ON public.consultation_slots TO authenticated;
GRANT ALL ON public.consultation_slots TO service_role;
ALTER TABLE public.consultation_slots ENABLE ROW LEVEL SECURITY;
CREATE POLICY consultation_read ON public.consultation_slots FOR SELECT TO authenticated USING (
 doctor_id = auth.uid() OR patient_id = auth.uid() OR (
 patient_id IS NULL AND starts_at > now() AND public.has_role(auth.uid(), 'patient') AND EXISTS (
 SELECT 1 FROM public.care_connections c WHERE c.patient_id = auth.uid() AND c.doctor_id = consultation_slots.doctor_id AND c.status = 'approved'
 ))
);
CREATE POLICY consultation_publish ON public.consultation_slots FOR INSERT TO authenticated WITH CHECK (
 doctor_id = auth.uid() AND public.has_role(auth.uid(), 'doctor') AND patient_id IS NULL AND booked_at IS NULL AND starts_at > now()
);
CREATE POLICY consultation_remove ON public.consultation_slots FOR DELETE TO authenticated USING (
 doctor_id = auth.uid() AND public.has_role(auth.uid(), 'doctor') AND patient_id IS NULL
);
CREATE FUNCTION public.book_consultation(_slot_id uuid) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE s public.consultation_slots;
BEGIN
 IF auth.uid() IS NULL OR NOT public.has_role(auth.uid(), 'patient') THEN RAISE EXCEPTION 'Patient account required'; END IF;
 SELECT * INTO s FROM public.consultation_slots WHERE id = _slot_id FOR UPDATE;
 IF NOT FOUND OR s.patient_id IS NOT NULL OR s.starts_at <= now() THEN RAISE EXCEPTION 'Slot unavailable'; END IF;
 IF NOT public.has_role(s.doctor_id, 'doctor') OR NOT EXISTS (SELECT 1 FROM public.care_connections c WHERE c.patient_id = auth.uid() AND c.doctor_id = s.doctor_id AND c.status = 'approved') THEN RAISE EXCEPTION 'Approved connection required'; END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended(auth.uid()::text, 0));
 IF EXISTS (SELECT 1 FROM public.consultation_slots WHERE patient_id = auth.uid() AND starts_at < s.ends_at AND ends_at > s.starts_at) THEN RAISE EXCEPTION 'Overlapping consultation'; END IF;
 UPDATE public.consultation_slots SET patient_id = auth.uid(), booked_at = now() WHERE id = s.id;
 RETURN s.id;
END $$;
REVOKE ALL ON FUNCTION public.book_consultation(uuid) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.book_consultation(uuid) TO authenticated;
CREATE FUNCTION public.cancel_consultation(_slot_id uuid) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
 UPDATE public.consultation_slots SET patient_id = NULL, booked_at = NULL WHERE id = _slot_id AND patient_id = auth.uid() AND starts_at > now();
 IF NOT FOUND THEN RAISE EXCEPTION 'Consultation unavailable'; END IF;
END $$;
REVOKE ALL ON FUNCTION public.cancel_consultation(uuid) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.cancel_consultation(uuid) TO authenticated;