'use client'

import type React from 'react'
import { Badge } from './ui/badge'
import { Button } from '@/components/ui/button'
import {
  Briefcase,
  CheckCircle2,
  Download,
  ExternalLink,
  FileText,
  MapPin,
  Phone,
  ShieldCheck,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface ResponseCardProps {
  type: string
  data: any
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-sm font-semibold text-slate-900">{value}</div>
    </div>
  )
}

export default function ResponseCard({ type, data }: ResponseCardProps) {
  const { t } = useTranslation()

  if ((type === 'automation' || type === 'service_lookup') && (data?.automation || data?.tourism_entities || data?.tool_context)) {
    return (
      <div className="space-y-3">
        {data.automation ? <AutomationCard automation={data.automation} /> : null}
        {data.tourism_entities ? <TourismEntitiesCard lookup={data.tourism_entities} /> : null}
        {data.tool_context?.tourism_entities && !data.tourism_entities ? (
          <TourismEntitiesCard lookup={data.tool_context.tourism_entities} />
        ) : null}
      </div>
    )
  }

  if (type === 'general' && data?.tool_context && Object.keys(data.tool_context).length > 0) {
    return (
      <div className="space-y-3">
        {data.tool_context.automation && (
          <AutomationCard automation={data.tool_context.automation} />
        )}

        {data.tool_context.tourism_entities && (
          <TourismEntitiesCard lookup={data.tool_context.tourism_entities} />
        )}

        {data.tool_context.insurance_quote && (
          <ServiceCard title="Generated insurance quote" tone="blue" icon={<ShieldCheck className="h-5 w-5 text-blue-700" />}>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field
                label="Annual premium"
                value={`${data.tool_context.insurance_quote.quote.premium_rwf?.toLocaleString()} RWF`}
              />
              <Field label="Location" value={data.tool_context.insurance_quote.input.location} />
            </div>
            <StepList steps={data.tool_context.insurance_quote.next_steps} />
            <p className="mt-3 text-xs text-slate-500">{data.tool_context.insurance_quote.quote.disclaimer}</p>
          </ServiceCard>
        )}

        {data.tool_context.business_requirements && (
          <ServiceCard title="Business registration walkthrough" tone="violet" icon={<Briefcase className="h-5 w-5 text-violet-700" />}>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Entity type" value={data.tool_context.business_requirements.entity_type} />
              <Field label="Timeline" value={data.tool_context.business_requirements.timeline} />
            </div>
            <StepList steps={data.tool_context.business_requirements.steps?.map((step: any) => step.title)} />
          </ServiceCard>
        )}

        {data.tool_context.prefilled_form && (
          <ServiceCard title="Prefilled registration draft" tone="violet" icon={<FileText className="h-5 w-5 text-violet-700" />}>
            <div className="grid gap-2 sm:grid-cols-2">
              {Object.entries(data.tool_context.prefilled_form.fields || {}).map(([key, value]) => (
                <Field key={key} label={key.replace(/_/g, ' ')} value={String(value || 'Missing')} />
              ))}
            </div>
            {data.tool_context.prefilled_form.missing_fields?.length ? (
              <p className="mt-3 text-xs font-medium text-amber-700">
                Missing: {data.tool_context.prefilled_form.missing_fields.join(', ')}
              </p>
            ) : null}
          </ServiceCard>
        )}

        {data.tool_context.agriculture_plan && (
          <ServiceCard title="Agriculture action plan" tone="lime" icon={<CheckCircle2 className="h-5 w-5 text-lime-700" />}>
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="Crop" value={data.tool_context.agriculture_plan.crop} />
              <Field label="District" value={data.tool_context.agriculture_plan.district} />
              <Field label="Month" value={data.tool_context.agriculture_plan.month} />
            </div>
            <StepList steps={data.tool_context.agriculture_plan.steps?.map((step: any) => step.title)} />
            <p className="mt-3 text-xs text-slate-600">{data.tool_context.agriculture_plan.tips}</p>
          </ServiceCard>
        )}

        {data.tool_context.tourism_walkthrough && (
          <ServiceCard title="Tourism service walkthrough" tone="emerald" icon={<MapPin className="h-5 w-5 text-emerald-700" />}>
            <StepList steps={data.tool_context.tourism_walkthrough.steps?.map((step: any) => step.title)} />
          </ServiceCard>
        )}

        {data.tool_context.accessibility_walkthrough && (
          <ServiceCard title="Accessibility walkthrough" tone="amber" icon={<CheckCircle2 className="h-5 w-5 text-amber-700" />}>
            <StepList steps={data.tool_context.accessibility_walkthrough.steps?.map((step: any) => step.title)} />
            <p className="mt-3 text-xs text-slate-600">Use this to simplify procedures for users with low literacy, disability, or limited connectivity.</p>
          </ServiceCard>
        )}
      </div>
    )
  }

  if (type === 'insurance_quote') {
    return (
      <div className="rounded-md border border-blue-200 bg-blue-50/70 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-blue-700" />
            <h3 className="text-sm font-semibold text-slate-900">{t('cards.insurance_quote')}</h3>
          </div>
          <Badge variant="outline" className="rounded-md border-blue-300 bg-white text-blue-700">
            Demo quote
          </Badge>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <Field label={t('cards.annual_premium')} value={`${data.premium_rwf?.toLocaleString()} RWF`} />
          <Field label={t('cards.coverage')} value={data.coverage?.third_party_liability} />
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Button size="sm" className="h-8 bg-slate-950 hover:bg-slate-800">
            <Phone className="h-4 w-4" />
            {t('cards.request_callback')}
          </Button>
        </div>
        <p className="mt-3 text-xs leading-5 text-slate-500">{data.disclaimer}</p>
      </div>
    )
  }

  if (type === 'itinerary') {
    return (
      <div className="rounded-md border border-emerald-200 bg-emerald-50/70 p-4">
        <div className="flex items-center gap-2">
          <MapPin className="h-5 w-5 text-emerald-700" />
          <h3 className="text-sm font-semibold text-slate-900">{t('cards.suggested_itinerary')}</h3>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <Field label={t('cards.title')} value={data.title} />
          <Field label={t('cards.duration')} value={data.duration} />
          <Field label={t('cards.estimated_cost')} value={data.estimated_cost} />
        </div>
        <div className="mt-4 space-y-2">
          {data.activities?.map((item: string) => (
            <div key={item} className="flex items-center gap-2 text-sm text-slate-700">
              <CheckCircle2 className="h-4 w-4 text-emerald-700" />
              {item}
            </div>
          ))}
        </div>
        <Button size="sm" className="mt-4 h-8 bg-slate-950 hover:bg-slate-800">
          <MapPin className="h-4 w-4" />
          {t('cards.open_map')}
        </Button>
      </div>
    )
  }

  if (type === 'farmer_tips') {
    return (
      <div className="rounded-md border border-lime-200 bg-lime-50/70 p-4">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-5 w-5 text-lime-700" />
          <h3 className="text-sm font-semibold text-slate-900">{t('cards.farming_tips')}</h3>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <Field label={t('cards.crop')} value={data.crop} />
          <Field label={t('cards.district')} value={data.district} />
        </div>
        <div className="mt-4 rounded-md border border-slate-200 bg-white p-3">
          <div className="text-xs uppercase tracking-wide text-slate-500">{t('cards.this_month_activities')}</div>
          <div className="mt-3 space-y-2">
            {data.month_tips?.map((item: string) => (
              <div key={item} className="flex items-center gap-2 text-sm text-slate-700">
                <CheckCircle2 className="h-4 w-4 text-lime-700" />
                {item}
              </div>
            ))}
          </div>
        </div>
        <Button size="sm" className="mt-4 h-8 bg-slate-950 hover:bg-slate-800">
          <Download className="h-4 w-4" />
          {t('cards.download_checklist')}
        </Button>
      </div>
    )
  }

  if (type === 'biz_steps') {
    return (
      <div className="rounded-md border border-violet-200 bg-violet-50/70 p-4">
        <div className="flex items-center gap-2">
          <Briefcase className="h-5 w-5 text-violet-700" />
          <h3 className="text-sm font-semibold text-slate-900">{t('cards.business_registration')}</h3>
        </div>
        <div className="mt-4">
          <Field label={t('cards.entity_type')} value={data.entity_type} />
        </div>
        <div className="mt-4 rounded-md border border-slate-200 bg-white p-3">
          <div className="text-xs uppercase tracking-wide text-slate-500">{t('cards.steps')}</div>
          <div className="mt-3 space-y-2">
            {data.steps?.map((item: string) => (
              <div key={item} className="flex items-start gap-2 text-sm text-slate-700">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-violet-700" />
                {item}
              </div>
            ))}
          </div>
        </div>
        <Button size="sm" className="mt-4 h-8 bg-slate-950 hover:bg-slate-800">
          <ExternalLink className="h-4 w-4" />
          {t('cards.open_portal')}
        </Button>
      </div>
    )
  }

  return null
}

function AutomationCard({ automation }: { automation: any }) {
  const tone: 'blue' | 'violet' | 'emerald' =
    automation.category === 'insurance' ? 'blue' : automation.category === 'tourism' ? 'emerald' : 'violet'
  const iconColor =
    automation.category === 'insurance' ? 'text-blue-700' : automation.category === 'tourism' ? 'text-emerald-700' : 'text-violet-700'
  const statusLabel = automation.status === 'ready' ? 'Ready' : 'Needs input'
  const link = automation.official_url || automation.portal_url

  return (
    <ServiceCard title={automation.title || 'Service automation'} tone={tone} icon={<FileText className={`h-5 w-5 ${iconColor}`} />}>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="rounded-md bg-white text-[10px] uppercase tracking-wide">
          {statusLabel}
        </Badge>
        {automation.last_reviewed ? (
          <span className="text-xs font-medium text-slate-500">Reviewed {automation.last_reviewed}</span>
        ) : null}
      </div>

      {automation.summary ? (
        <p className="text-sm leading-6 text-slate-700">{automation.summary}</p>
      ) : null}

      {automation.collected_fields?.length ? (
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {automation.collected_fields.map((field: any) => (
            <Field key={field.id} label={field.label} value={String(field.value)} />
          ))}
        </div>
      ) : null}

      {automation.missing_fields?.length ? (
        <div className="mt-4 rounded-md border border-amber-200 bg-white p-3">
          <div className="text-xs font-bold uppercase tracking-wide text-amber-700">Required details</div>
          <div className="mt-3 space-y-3">
            {automation.missing_fields.map((field: any) => (
              <div key={field.id} className="text-sm text-slate-700">
                <p className="font-semibold">{field.prompt}</p>
                {field.options?.length ? (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {field.options.map((option: any) => (
                      <span key={option.id} className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-medium text-slate-600">
                        {option.label}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <StepList steps={automation.steps} />

      {automation.next_actions?.length ? (
        <div className="mt-4 rounded-md border border-slate-200 bg-white p-3">
          <div className="text-xs font-bold uppercase tracking-wide text-slate-500">Next actions</div>
          <StepList steps={automation.next_actions} />
        </div>
      ) : null}

      {link ? (
        <a
          href={link}
          target="_blank"
          rel="noreferrer"
          className="mt-4 inline-flex h-8 items-center gap-2 rounded-md bg-slate-950 px-3 text-xs font-semibold text-white transition hover:bg-slate-800"
        >
          <ExternalLink className="h-4 w-4" />
          Open official page
        </a>
      ) : null}

      {automation.source ? (
        <p className="mt-3 text-xs leading-5 text-slate-500">Source: {automation.source}</p>
      ) : null}
    </ServiceCard>
  )
}

function TourismEntitiesCard({ lookup }: { lookup: any }) {
  const matches = lookup.matches || []

  return (
    <ServiceCard title={lookup.title || 'Licensed tourism entity lookup'} tone="emerald" icon={<ShieldCheck className="h-5 w-5 text-emerald-700" />}>
      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="Status" value={lookup.status || 'unknown'} />
        <Field label="Cached records" value={lookup.total_cached?.toLocaleString?.() || lookup.total_cached || '0'} />
        <Field label="Last synced" value={lookup.last_synced ? String(lookup.last_synced).slice(0, 10) : 'Not synced'} />
      </div>

      {lookup.message ? (
        <p className="mt-3 text-sm leading-6 text-slate-700">{lookup.message}</p>
      ) : null}

      {matches.length ? (
        <div className="mt-4 space-y-2">
          {matches.slice(0, 6).map((entity: any) => (
            <div key={`${entity.name}-${entity.profile_url}`} className="rounded-md border border-slate-200 bg-white p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-bold text-slate-900">{entity.name}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-600">
                    {entity.sub_category || entity.category} - {entity.district}, {entity.province}
                  </p>
                </div>
                <Badge variant="outline" className="rounded-md bg-emerald-50 text-[10px] uppercase tracking-wide text-emerald-700">
                  {entity.status || 'Listed'}
                </Badge>
              </div>
              {entity.profile_url ? (
                <a
                  href={entity.profile_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-800"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  Registry profile
                </a>
              ) : null}
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-4 rounded-md border border-amber-200 bg-white p-3 text-sm text-slate-700">
          No matching licensed entity was found in the cached registry.
        </p>
      )}

      {lookup.source_url ? (
        <a
          href={lookup.source_url}
          target="_blank"
          rel="noreferrer"
          className="mt-4 inline-flex h-8 items-center gap-2 rounded-md bg-slate-950 px-3 text-xs font-semibold text-white transition hover:bg-slate-800"
        >
          <ExternalLink className="h-4 w-4" />
          Open official registry
        </a>
      ) : null}
    </ServiceCard>
  )
}

function ServiceCard({
  title,
  tone,
  icon,
  children,
}: {
  title: string
  tone: 'blue' | 'violet' | 'lime' | 'emerald' | 'amber'
  icon: React.ReactNode
  children: React.ReactNode
}) {
  const classes = {
    blue: 'border-blue-200 bg-blue-50/70',
    violet: 'border-violet-200 bg-violet-50/70',
    lime: 'border-lime-200 bg-lime-50/70',
    emerald: 'border-emerald-200 bg-emerald-50/70',
    amber: 'border-amber-200 bg-amber-50/70',
  }

  return (
    <div className={`rounded-md border p-4 ${classes[tone]}`}>
      <div className="mb-4 flex items-center gap-2">
        {icon}
        <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      </div>
      {children}
    </div>
  )
}

function StepList({ steps }: { steps?: string[] }) {
  if (!steps?.length) return null

  return (
    <div className="mt-4 space-y-2">
      {steps.map((step, index) => (
        <div key={`${step}-${index}`} className="flex items-start gap-2 text-sm text-slate-700">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-slate-600" />
          <span>{step}</span>
        </div>
      ))}
    </div>
  )
}
