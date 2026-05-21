import { useMemo, useState, type ReactNode } from "react";
import { Eye, MessageSquareText, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type ScenarioStatus = "ready" | "blocked";

type MessageScenario = {
  id: string;
  title: string;
  input: string[];
  decision: string;
  message: string | null;
  reason: string;
  status: ScenarioStatus;
};

const demoValues = {
  clientName: "Анна",
  serviceWithBooking: "Вечерний макияж",
  serviceWithoutBooking: "Стрижка женская",
  masterName: "Мария",
  appointmentDate: "22 мая",
  appointmentTime: "14:30",
  bookingLink: "https://example.com/booking",
};

const withoutBookingMessage = `${demoValues.clientName}, добрый день ☀️
Это бьюти-пространство «ВНЕ РАМОК». Ваша запись на процедуру:
🧖️♀️ Процедура: ${demoValues.serviceWithoutBooking}
💇️ ♀️ К эксперту: ${demoValues.masterName}
📅 Дата: ${demoValues.appointmentDate}
🕰️ Время: ${demoValues.appointmentTime}

🔗 Подробнее о записи: ${demoValues.bookingLink}
🚗 Парковка (три въезда):
👉 Со стороны Сибгата Хакима, сразу после Татнефть Арены.
👉 Со стороны Мусина, следующий поворот направо после первого поворота
после Татнефть Арены.
👉 Со стороны Чистопольской.
Для того чтобы мы открыли вам шлагбаум, пожалуйста, позвоните нам, когда
будете у него.
💰 3% кешбэка при расчёте наличными на ваш внутренний счёт в пространстве.
Наши официальные источники:
📸 Instagram: instagram.com/vneramok.kzn
📱 Telegram-канал: t.me/vneramok_kzn
📘 ВКонтакте: vk.com/vneramok_kzn
📍 Как к нам добраться:
Казань, ул. Сибгата Хакима, 17
📞 Телефон: +7 993 063 6360
🗺️ [Карта] (clck.ru/3BDCZa)
До скорой встречи в пространстве, где границы существуют, чтобы их расширять
💚
С заботой, команда «ВНЕ РАМОК»`;

const withBookingMessage = `${demoValues.clientName}, добрый день ☀️
Это бьюти-пространство «ВНЕ РАМОК». Ваша запись на процедуру:
🧖️♀️ Процедура: ${demoValues.serviceWithBooking}
💇️ ♀️ К эксперту: ${demoValues.masterName}
📅 Дата: ${demoValues.appointmentDate}
🕰️ Время: ${demoValues.appointmentTime}
⏳ Для бронирования времени вашей записи необходимо перевести сумму
бронирования в размере 1000 ₽:
✔️ Пришлите скрин об оплате, чтобы подтвердить запись
✔️ Бронирование входит в стоимость вашей процедуры
✔️ При отмене брони предоплата возвращается, если до назначенного времени
остаётся более 24 часов
✔️ При переносе брони (не больше 2 раз) предоплата возвращается, если до
назначенного времени остаётся более 24 часов
✔️ Таким образом студия подстраховывает себя, так как мы уже не успеем открыть
это время для других клиентов
🙏🏼 Искренне надеемся на ваше понимание.
🔗 Подробнее о записи: ${demoValues.bookingLink}
🚗 Парковка (три въезда):
👉 Со стороны Сибгата Хакима, сразу после Татнефть Арены
👉 Со стороны Мусина, следующий поворот направо после первого поворота
после Татнефть Арены
👉 Со стороны Чистопольской
Для того чтобы мы открыли вам шлагбаум, пожалуйста, позвоните нам, когда
будете у него.
💰 3% кешбэка при расчёте наличными на ваш внутренний счёт в пространстве.
Наши официальные источники:
📸 Instagram: instagram.com/vneramok.kzn
📱 Telegram-канал: t.me/vneramok_kzn
📘 ВКонтакте: vk.com/vneramok_kzn
📍 Как к нам добраться:
Казань, ул. Сибгата Хакима, 17
📞 Телефон: +7 993 063 6360
🗺️ [Карта] (clck.ru/3BDCZa)
До скорой встречи в пространстве, где границы существуют, чтобы их расширять
💚
С заботой, команда «ВНЕ РАМОК»`;

const reminder24hMessage = `${demoValues.clientName}, добрый день ☀️
Это бьюти-пространство «ВНЕ РАМОК». Напоминаем, что через 24 часа у вас запланирована процедура «${demoValues.serviceWithBooking}» 🤩
Пожалуйста, подтвердите свою запись, перейдя по ссылке ниже и нажав кнопку
«Подтвердить» – это займёт всего секунду, но поможет нам подготовиться к
вашей встрече с душой 💚
Если по какой-то причине не получается прийти – просто напишите нам,
отменим или перенесём без проблем. На ваше время действительно есть
желающие, поэтому неподтверждённая запись будет вынужденно освобождена.
📅 Дата: ${demoValues.appointmentDate}
⏰ Время: ${demoValues.appointmentTime}
💆️ ♀️ Услуга: ${demoValues.serviceWithBooking}
🔗 Подтверждение (и детали): ${demoValues.bookingLink}
📍 Как к нам добраться:
Казань, ул. Сибгата Хакима, 17

📞 Телефон: +7 993 063 6360
🗺️ [Карта] (clck.ru/3BDCZa)
Наши официальные источники:
📸 Instagram: instagram.com/vneramok.kzn
📱 Telegram-канал: t.me/vneramok_kzn
📘 ВКонтакте: vk.com/vneramok_kzn
Будем рады видеть вас в пространстве, где границы существуют, чтобы их
расширять 💚
Ждём вашего подтверждения или сообщения 🌸`;

const reminder2hMessage = `${demoValues.clientName}, добрый день ☀️
Это бьюти-пространство «ВНЕ РАМОК». Напоминаем, что через 2 часа у вас запланирована процедура «${demoValues.serviceWithBooking}» 🤩
Уже совсем скоро увидимся! Приходите – мы ждём вас, чтобы вместе сделать то,
что вам давно хотелось, бережно и с душой 💚
📅 Дата: ${demoValues.appointmentDate}
⏰ Время: ${demoValues.appointmentTime}
💆️ ♀️ Услуга: ${demoValues.serviceWithBooking}
🔗 Детали: ${demoValues.bookingLink}
📍 Как к нам добраться:
Казань, ул. Сибгата Хакима, 17
📞 Телефон: +7 993 063 6360
🗺️ [Карта] (clck.ru/3BDCZa)
Наши официальные источники:
📸 Instagram: instagram.com/vneramok.kzn
📱 Telegram-канал: t.me/vneramok_kzn
📘 ВКонтакте: vk.com/vneramok_kzn
До встречи в пространстве, где границы существуют, чтобы их расширять 💚
Если вдруг что-то изменилось – просто напишите, мы рядом 🌸`;

const rescheduledMessage = `${demoValues.clientName}, добрый день ☀️
Это бьюти-пространство «ВНЕ РАМОК». Уведомляем вас о переносе записи:
📅 Дата: ${demoValues.appointmentDate}
🕰️ Время: ${demoValues.appointmentTime}
💆️ ♀️ Услуга: ${demoValues.serviceWithBooking}
Если у вас возникнут вопросы или потребуется скорректировать время – просто
напишите нам, мы всегда рядом 💚
Наши официальные источники:
📸 Instagram: instagram.com/vneramok.kzn
📱 Telegram-канал: t.me/vneramok_kzn
📘 ВКонтакте: vk.com/vneramok_kzn

📍 Как к нам добраться:
Казань, ул. Сибгата Хакима, 17
📞 Телефон: +7 993 063 6360
🗺️ [Карта] (clck.ru/3BDCZa)
С заботой, команда бьюти-пространства «ВНЕ РАМОК» 💚`;

const cancelledMessage = `${demoValues.clientName}, добрый день ☀️
Это бьюти-пространство «ВНЕ РАМОК». Уведомляем вас об отмене записи:
📅 Дата: ${demoValues.appointmentDate}
🕰️ Время: ${demoValues.appointmentTime}
💆️ ♀️ Услуга: ${demoValues.serviceWithBooking}
Если вы захотите записаться снова или у вас есть вопросы – мы всегда на связи
💚
Наши официальные источники:
📸 Instagram: instagram.com/vneramok.kzn
📱 Telegram-канал: t.me/vneramok_kzn
📘 ВКонтакте: vk.com/vneramok_kzn
📍 Как к нам добраться:
Казань, ул. Сибгата Хакима, 17
📞 Телефон: +7 993 063 6360
🗺️ [Карта] (clck.ru/3BDCZa)
С заботой, команда бьюти-пространства «ВНЕ РАМОК» 💚`;

const scenarios: MessageScenario[] = [
  {
    id: "without-booking",
    title: "Запись без бронирования",
    input: [
      "Создана запись",
      `Услуга: ${demoValues.serviceWithoutBooking}`,
      `Клиент: ${demoValues.clientName}`,
      `Дата и время: ${demoValues.appointmentDate}, ${demoValues.appointmentTime}`,
    ],
    decision: "Услуга не относится к списку услуг с бронированием. Показываем обычное сообщение о созданной записи.",
    message: withoutBookingMessage,
    reason: "Это демонстрационный предпросмотр. Реальная отправка отключена.",
    status: "ready",
  },
  {
    id: "with-booking",
    title: "Запись с бронированием",
    input: [
      "Создана запись",
      `Услуга: ${demoValues.serviceWithBooking}`,
      `Клиент: ${demoValues.clientName}`,
      `Дата и время: ${demoValues.appointmentDate}, ${demoValues.appointmentTime}`,
    ],
    decision: "Услуга найдена в списке услуг с бронированием. Показываем сообщение с блоком бронирования.",
    message: withBookingMessage,
    reason: "Это демонстрационный предпросмотр. Реальная отправка отключена.",
    status: "ready",
  },
  {
    id: "reminder-24h",
    title: "Напоминание за 24 часа",
    input: [
      "До записи осталось 24 часа",
      `Клиент: ${demoValues.clientName}`,
      `Услуга: ${demoValues.serviceWithBooking}`,
      `Дата: ${demoValues.appointmentDate}`,
      `Время: ${demoValues.appointmentTime}`,
      `Специалист: ${demoValues.masterName}`,
      `Ссылка: ${demoValues.bookingLink}`,
    ],
    decision: "Показываем клиенту напоминание о записи за 24 часа.",
    message: reminder24hMessage,
    reason: "Сообщение не отправляется. Это только предпросмотр.",
    status: "ready",
  },
  {
    id: "reminder-2h",
    title: "Напоминание за 2 часа",
    input: [
      "До записи осталось 2 часа",
      `Клиент: ${demoValues.clientName}`,
      `Услуга: ${demoValues.serviceWithBooking}`,
      `Дата: ${demoValues.appointmentDate}`,
      `Время: ${demoValues.appointmentTime}`,
      `Специалист: ${demoValues.masterName}`,
      `Ссылка: ${demoValues.bookingLink}`,
    ],
    decision: "Показываем клиенту напоминание о записи за 2 часа.",
    message: reminder2hMessage,
    reason: "Сообщение не отправляется. Это только предпросмотр.",
    status: "ready",
  },
  {
    id: "rescheduled",
    title: "Уведомление об изменении записи",
    input: [
      "Запись перенесена",
      `Клиент: ${demoValues.clientName}`,
      `Услуга: ${demoValues.serviceWithBooking}`,
      `Новая дата: ${demoValues.appointmentDate}`,
      `Новое время: ${demoValues.appointmentTime}`,
    ],
    decision: "Показываем клиенту сообщение о переносе записи.",
    message: rescheduledMessage,
    reason: "Сообщение не отправляется. Это только предпросмотр.",
    status: "ready",
  },
  {
    id: "cancelled",
    title: "Уведомление об удалении записи",
    input: [
      "Запись отменена",
      `Клиент: ${demoValues.clientName}`,
      `Услуга: ${demoValues.serviceWithBooking}`,
      `Дата: ${demoValues.appointmentDate}`,
      `Время: ${demoValues.appointmentTime}`,
    ],
    decision: "Показываем клиенту сообщение об отмене записи.",
    message: cancelledMessage,
    reason: "Сообщение не отправляется. Это только предпросмотр.",
    status: "ready",
  },
  {
    id: "unknown-service",
    title: "Неизвестная услуга",
    input: ["Создана запись", "Услуга: не найдена в списке Flow Sell", `Клиент: ${demoValues.clientName}`],
    decision: "Сообщение не формируется автоматически. Нужна ручная проверка услуги.",
    message: null,
    reason: "Нельзя безопасно определить, нужен ли блок бронирования.",
    status: "blocked",
  },
  {
    id: "empty-service",
    title: "Пустая услуга",
    input: ["Создана запись", "Услуга: не указана", `Клиент: ${demoValues.clientName}`],
    decision: "Сообщение не формируется автоматически. Нужна ручная проверка.",
    message: null,
    reason: "Нет названия услуги, поэтому нельзя выбрать правильный текст.",
    status: "blocked",
  },
  {
    id: "removed-service",
    title: "Услуга удалена",
    input: ["Создана запись", "Услуга: Услуга удалена", `Клиент: ${demoValues.clientName}`],
    decision: "Сообщение не формируется автоматически до подтверждения заказчика.",
    message: null,
    reason: "Название выглядит как системное или удалённое, есть риск показать клиенту некорректный текст.",
    status: "blocked",
  },
];

export function MessagePreviewPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selectedScenario = useMemo(
    () => scenarios.find((scenario) => scenario.id === selectedId) ?? null,
    [selectedId],
  );

  return (
    <main className="mx-auto max-w-7xl space-y-6 px-4 py-6">
      <section className="rounded-2xl border border-border bg-card p-5 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="space-y-2">
            <Badge variant="outline" className="w-fit">
              Customer Preview
            </Badge>
            <h2 className="text-2xl font-semibold tracking-tight">Предпросмотр сообщений</h2>
            <p className="max-w-3xl text-sm text-muted-foreground">
              Это демонстрация сообщений. Реальные сообщения клиентам не отправляются.
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-xl border border-border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
            <ShieldCheck className="h-4 w-4 text-green-300" />
            Только просмотр
          </div>
        </div>
      </section>

      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {scenarios.map((scenario) => (
          <button
            key={scenario.id}
            type="button"
            onClick={() => setSelectedId(scenario.id)}
            className={cn(
              "rounded-lg border bg-card p-4 text-left shadow-sm transition hover:border-primary/70 hover:bg-muted/30",
              selectedId === scenario.id ? "border-primary ring-2 ring-primary/30" : "border-border",
            )}
          >
            <div className="mb-3 flex items-start justify-between gap-2">
              <h3 className="text-sm font-semibold leading-snug">{scenario.title}</h3>
              <Badge variant={scenario.status === "ready" ? "success" : "secondary"}>
                не отправляется
              </Badge>
            </div>
            <p className="text-xs leading-5 text-muted-foreground">{scenario.decision}</p>
          </button>
        ))}
      </section>

      {!selectedScenario ? (
        <Card className="border-dashed">
          <CardContent className="flex min-h-[320px] flex-col items-center justify-center gap-3 text-center">
            <Eye className="h-10 w-10 text-muted-foreground" />
            <div>
              <h3 className="text-base font-semibold">Выберите сценарий</h3>
              <p className="mt-1 max-w-md text-sm text-muted-foreground">
                Здесь появится ready state: входные данные, решение и сообщение в человеческом виде.
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <section className="grid gap-4 lg:grid-cols-[360px_minmax(0,1fr)]">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <MessageSquareText className="h-5 w-5" />
                {selectedScenario.title}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <PreviewBlock title="Сценарий">
                <p>{selectedScenario.title}</p>
              </PreviewBlock>

              <PreviewBlock title="Входные данные">
                <ul className="space-y-1">
                  {selectedScenario.input.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </PreviewBlock>

              <PreviewBlock title="Какое решение принято">
                <p>{selectedScenario.decision}</p>
              </PreviewBlock>

              <PreviewBlock title="Статус">
                <Badge variant="secondary">не отправляется</Badge>
                <p className="mt-2 text-sm text-muted-foreground">{selectedScenario.reason}</p>
              </PreviewBlock>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Итоговое сообщение</CardTitle>
              <p className="text-sm text-muted-foreground">Такой текст увидел бы клиент в демо-сценарии.</p>
            </CardHeader>
            <CardContent>
              {selectedScenario.message ? (
                <div className="whitespace-pre-wrap rounded-xl border border-border bg-background p-4 text-sm leading-6">
                  {selectedScenario.message}
                </div>
              ) : (
                <div className="flex min-h-[260px] flex-col items-center justify-center rounded-xl border border-dashed border-border bg-muted/20 p-6 text-center">
                  <h3 className="text-base font-semibold">Сообщение не формируется</h3>
                  <p className="mt-2 max-w-md text-sm text-muted-foreground">{selectedScenario.reason}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </section>
      )}
    </main>
  );
}

function PreviewBlock({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{title}</h4>
      <div className="text-sm leading-6">{children}</div>
    </div>
  );
}
