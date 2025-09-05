import { getDictionary } from '../../../../../get-dictionary';
import { Locale } from '../../../../../i18n-config';
import ChatPageClient from '../../components/ChatPageClient';

export default async function ChatPage({
  params,
}: {
  params: { lang: Locale; chatId: string };
}) {
  const dictionary = await getDictionary(params.lang);

  return <ChatPageClient dictionary={dictionary} chatId={params.chatId} />;
}