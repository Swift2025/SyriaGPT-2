// src/app/[lang]/chat/[chatId]/page.tsx
import { getDictionary } from '../../../../../get-dictionary';
import { Locale } from '../../../../../i18n-config';
import ChatPageClient from '../../components/ChatPageClient';

export default async function ChatPage({
  params: awaitedParams,
}: {
  params: { lang: Locale; chatId: string };
}) {
  const params = await awaitedParams;
  const lang = params.lang;
  const chatId = params.chatId;

  const dictionary = await getDictionary(lang);

  return <ChatPageClient dictionary={dictionary} chatId={chatId} />;
}
